from celery import shared_task
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.utils import timezone

from .models import Certificate, GenerationJob
from .services.certificate_generator import generate_certificate_pdf


@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def generate_job_certificates(self, job_id):
    try:
        job = GenerationJob.objects.get(pk=job_id)
    except GenerationJob.DoesNotExist:
        return {"job_id": job_id, "status": "missing"}

    if job.status in {GenerationJob.Status.COMPLETED, GenerationJob.Status.COMPLETED_WITH_ERRORS}:
        return {"job_id": job_id, "status": job.status}

    GenerationJob.objects.filter(pk=job_id).update(
        status=GenerationJob.Status.PROCESSING,
        started_at=timezone.now(),
    )

    certificates = Certificate.objects.filter(
        job_id=job_id, status=Certificate.Status.PENDING
    ).order_by("created_at")

    try:
        for certificate in certificates.iterator():
            try:
                Certificate.objects.filter(pk=certificate.pk).update(
                    status=Certificate.Status.PROCESSING
                )
                job = GenerationJob.objects.get(pk=job_id)
                pdf_bytes = generate_certificate_pdf(
                    recipient_name=certificate.recipient_name,
                    certificate_title=job.certificate_title,
                    event_name=job.event_name,
                    event_date=job.event_date,
                    issuer_name=job.issuer_name,
                    issuer_title=job.issuer_title,
                    certificate_number=certificate.certificate_number,
                )
                certificate.file.save(
                    f"{certificate.certificate_number}.pdf",
                    ContentFile(pdf_bytes),
                    save=False,
                )
                certificate.status = Certificate.Status.COMPLETED
                certificate.completed_at = timezone.now()
                certificate.error_message = ""
                certificate.save(
                    update_fields=["file", "status", "completed_at", "error_message"]
                )
            except Exception as exc:
                # A recipient-specific failure is recorded and processing continues.
                Certificate.objects.filter(pk=certificate.pk).update(
                    status=Certificate.Status.FAILED,
                    error_message=str(exc)[:2000],
                    completed_at=timezone.now(),
                )
            finally:
                _refresh_job_progress(job_id)
    except Exception as exc:
        GenerationJob.objects.filter(pk=job_id).update(
            status=GenerationJob.Status.FAILED,
            error_message=str(exc)[:2000],
            completed_at=timezone.now(),
        )
        raise

    job = GenerationJob.objects.get(pk=job_id)
    if job.failed_count:
        job.status = GenerationJob.Status.COMPLETED_WITH_ERRORS
    else:
        job.status = GenerationJob.Status.COMPLETED
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "completed_at"])

    return {
        "job_id": str(job.id),
        "status": job.status,
        "successful_count": job.successful_count,
        "failed_count": job.failed_count,
    }


def _refresh_job_progress(job_id):
    counts = Certificate.objects.filter(job_id=job_id).aggregate(
        completed=Count("id", filter=Q(status=Certificate.Status.COMPLETED)),
        failed=Count("id", filter=Q(status=Certificate.Status.FAILED)),
    )
    processed = counts["completed"] + counts["failed"]
    GenerationJob.objects.filter(pk=job_id).update(
        processed_count=processed,
        successful_count=counts["completed"],
        failed_count=counts["failed"],
    )
