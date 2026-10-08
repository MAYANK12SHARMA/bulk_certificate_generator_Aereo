from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_SIZE = landscape(A4)


def _fit_text(c, text, font_name, max_size, min_size, max_width):
    size = max_size
    while size > min_size and stringWidth(text, font_name, size) > max_width:
        size -= 1
    return size


def generate_certificate_pdf(*, recipient_name, certificate_title, event_name, event_date, issuer_name, issuer_title, certificate_number):
    """Generate one PDF using the application's single predefined template."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=PAGE_SIZE)
    width, height = PAGE_SIZE

    # Fixed template: border, header, recipient, event metadata, issuer and certificate number.
    margin = 28
    c.setStrokeColor(colors.HexColor("#1F2937"))
    c.setLineWidth(3)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#9CA3AF"))
    c.rect(margin + 10, margin + 10, width - 2 * (margin + 10), height - 2 * (margin + 10))

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 88, "CERTIFICATE")

    c.setFillColor(colors.HexColor("#374151"))
    title_size = _fit_text(c, certificate_title, "Helvetica-Bold", 22, 12, width - 160)
    c.setFont("Helvetica-Bold", title_size)
    c.drawCentredString(width / 2, height - 122, certificate_title)

    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 160, "This certificate is proudly presented to")

    name_size = _fit_text(c, recipient_name, "Helvetica-Bold", 30, 16, width - 180)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(width / 2, height - 205, recipient_name)

    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.line(width / 2 - 190, height - 220, width / 2 + 190, height - 220)

    c.setFillColor(colors.HexColor("#374151"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 252, f"for participation in {event_name}")

    if event_date:
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#6B7280"))
        c.drawCentredString(width / 2, height - 275, f"Event date: {event_date.strftime('%d %B %Y')}")

    issuer_y = 98
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width / 2, issuer_y + 22, issuer_name)
    if issuer_title:
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#6B7280"))
        c.drawCentredString(width / 2, issuer_y + 7, issuer_title)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#6B7280"))
    c.drawCentredString(width / 2, 42, f"Certificate No. {certificate_number}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
