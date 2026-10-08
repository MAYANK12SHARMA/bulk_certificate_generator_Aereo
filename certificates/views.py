from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Certificate, GenerationJob
from .serializers import (
    CertificateSerializer,
    GenerationJobCreateSerializer,
    GenerationJobSerializer,
)
from .tasks import generate_job_certificates


class GenerationJobCreateView(APIView):
    def post(self, request):
        serializer = GenerationJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        try:
            task = generate_job_certificates.delay(str(job.id))
        except Exception:
            job.status = GenerationJob.Status.FAILED
            job.error_message = "Unable to queue certificate generation task. Is Redis/Celery available?"
            job.save(update_fields=["status", "error_message"])
            return Response(
                GenerationJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "job_id": str(job.id),
                "status": job.status,
                "message": "Certificate generation job accepted.",
                "task_id": task.id,
                "status_url": request.build_absolute_uri(f"/api/jobs/{job.id}/"),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class GenerationJobDetailView(APIView):
    def get(self, request, job_id):
        job = get_object_or_404(GenerationJob, pk=job_id)
        return Response(GenerationJobSerializer(job, context={"request": request}).data)


class GetAllGenerationJobsView(APIView):
    def get(self, request):
        jobs = GenerationJob.objects.all()
        return Response(
            GenerationJobSerializer(jobs, many=True, context={"request": request}).data
        )


class GenerationJobCertificatesView(APIView):
    def get(self, request, job_id):
        job = get_object_or_404(GenerationJob, pk=job_id)
        certificates = job.certificates.all()
        return Response(
            CertificateSerializer(
                certificates, many=True, context={"request": request}
            ).data
        )


class CertificateDetailView(APIView):
    def get(self, request, certificate_id):
        certificate = get_object_or_404(Certificate, pk=certificate_id)
        return Response(
            CertificateSerializer(certificate, context={"request": request}).data
        )


class CertificateDownloadView(APIView):
    def get(self, request, certificate_id):
        certificate = get_object_or_404(Certificate, pk=certificate_id)
        if certificate.status != Certificate.Status.COMPLETED or not certificate.file:
            raise Http404("Certificate is not available for download.")
        return FileResponse(
            certificate.file.open("rb"),
            as_attachment=True,
            filename=f"{certificate.certificate_number}.pdf",
            content_type="application/pdf",
        )
