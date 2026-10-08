from django.contrib import admin
from .models import Certificate, GenerationJob


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        "id", "event_name", "status", "total_recipients", "successful_count",
        "failed_count", "processed_count", "created_at"
    )
    list_filter = ("status", "created_at")
    search_fields = ("event_name", "issuer_name")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "recipient_name", "recipient_email", "status", "job")
    list_filter = ("status", "created_at")
    search_fields = ("certificate_number", "recipient_name", "recipient_email")
