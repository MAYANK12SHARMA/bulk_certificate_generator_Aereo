from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from certificates.models import Certificate, GenerationJob
from certificates.tasks import generate_job_certificates


class GenerationJobAPITests(APITestCase):
    payload = {
        "event_name": "Django Workshop",
        "certificate_title": "Certificate of Participation",
        "event_date": "2026-10-08",
        "issuer_name": "Open Learning Club",
        "issuer_title": "Program Director",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ],
    }


    @patch("certificates.views.generate_job_certificates.delay")
    def test_create_generation_job(self, mock_delay):
        mock_delay.return_value.id = "task-123"
        response = self.client.post(reverse("job-create"), self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        job = GenerationJob.objects.get(id=response.data["job_id"])
        self.assertEqual(job.total_recipients, 2)
        self.assertEqual(Certificate.objects.filter(job=job).count(), 2)
        mock_delay.assert_called_once()

    def test_invalid_recipient_email_is_rejected(self):
        payload = {**self.payload, "recipients": [{"name": "Alice", "email": "bad-email"}]}
        response = self.client.post(reverse("job-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recipients", response.data)
        self.assertEqual(GenerationJob.objects.count(), 0)

    def test_duplicate_emails_are_rejected_case_insensitively(self):
        payload = {
            **self.payload,
            "recipients": [
                {"name": "Alice", "email": "Alice@example.com"},
                {"name": "Alicia", "email": "alice@example.com"},
            ],
        }
        response = self.client.post(reverse("job-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("certificates.views.generate_job_certificates.delay")
    def test_job_status_and_progress(self, mock_delay):
        mock_delay.return_value.id = "task-123"
        response = self.client.post(reverse("job-create"), self.payload, format="json")
        job_id = response.data["job_id"]

        job = GenerationJob.objects.get(id=job_id)
        job.status = GenerationJob.Status.PROCESSING
        job.processed_count = 1
        job.successful_count = 1
        job.save()

        detail = self.client.get(reverse("job-detail", kwargs={"job_id": job_id}))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["progress_percent"], 50.0)
        self.assertEqual(detail.data["processed_count"], 1)

    @patch("certificates.tasks.generate_certificate_pdf")
    def test_one_certificate_failure_does_not_stop_others(self, mock_generator):
        job = GenerationJob.objects.create(
            event_name="Failure Test",
            issuer_name="Issuer",
            total_recipients=2,
        )
        first = Certificate.objects.create(
            job=job,
            recipient_name="Alice",
            recipient_email="alice@example.com",
            certificate_number="CERT-FAILTEST-0001",
        )
        second = Certificate.objects.create(
            job=job,
            recipient_name="Bob",
            recipient_email="bob@example.com",
            certificate_number="CERT-FAILTEST-0002",
        )

        def side_effect(**kwargs):
            if kwargs["recipient_name"] == "Alice":
                raise RuntimeError("Intentional test failure")
            return b"%PDF-1.4 test pdf bytes"

        mock_generator.side_effect = side_effect
        result = generate_job_certificates.run(str(job.id))

        first.refresh_from_db()
        second.refresh_from_db()
        job.refresh_from_db()
        self.assertEqual(first.status, Certificate.Status.FAILED)
        self.assertIn("Intentional test failure", first.error_message)
        self.assertEqual(second.status, Certificate.Status.COMPLETED)
        self.assertEqual(result["successful_count"], 1)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(job.status, GenerationJob.Status.COMPLETED_WITH_ERRORS)
