from datetime import date
from io import BytesIO

from django.test import SimpleTestCase

from certificates.services.certificate_generator import generate_certificate_pdf


class CertificateGeneratorTests(SimpleTestCase):
    def test_generates_valid_pdf_bytes(self):
        pdf = generate_certificate_pdf(
            recipient_name="Mayank Sharma",
            certificate_title="Certificate of Participation",
            event_name="AI Workshop",
            event_date=date(2026, 10, 8),
            issuer_name="Example Organization",
            issuer_title="Program Director",
            certificate_number="CERT-TEST-0001",
        )

        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)
