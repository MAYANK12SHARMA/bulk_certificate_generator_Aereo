from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from certificates.models import Certificate, GenerationJob


class CertificateDownloadTests(APITestCase):
    def test_download_completed_certificate(self):
        job = GenerationJob.objects.create(event_name="Event", issuer_name="Issuer", total_recipients=1)
        certificate = Certificate.objects.create(
            job=job,
            recipient_name="Alice",
            recipient_email="alice@example.com",
            certificate_number="CERT-DOWNLOAD-0001",
            status=Certificate.Status.COMPLETED,
        )
        certificate.file.save("CERT-DOWNLOAD-0001.pdf", ContentFile(b"%PDF-1.4 test"), save=True)

        response = self.client.get(reverse("certificate-download", kwargs={"certificate_id": certificate.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
