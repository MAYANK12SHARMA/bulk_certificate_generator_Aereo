from django.db import transaction
from rest_framework import serializers
from .models import Certificate, GenerationJob


class RecipientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField()


class GenerationJobCreateSerializer(serializers.Serializer):
    event_name = serializers.CharField(max_length=200, allow_blank=False)
    certificate_title = serializers.CharField(
        max_length=200,
        required=False,
        default="Certificate of Participation",
    )
    event_date = serializers.DateField(required=False, allow_null=True)
    issuer_name = serializers.CharField(max_length=150, allow_blank=False)
    issuer_title = serializers.CharField(max_length=150, required=False, allow_blank=True)
    recipients = RecipientSerializer(many=True, allow_empty=False)

    def validate_recipients(self, recipients):
        if len(recipients) > 1000:
            raise serializers.ValidationError("A single job can contain at most 1000 recipients.")
        normalized = {item["email"].strip().lower() for item in recipients}
        if len(normalized) != len(recipients):
            raise serializers.ValidationError("Duplicate recipient email addresses are not allowed.")
        return recipients

    @transaction.atomic
    def create(self, validated_data):
        recipients = validated_data.pop("recipients")
        job = GenerationJob.objects.create(
            **validated_data,
            total_recipients=len(recipients),
        )
        certificate_rows = [
            Certificate(
                job=job,
                recipient_name=item["name"].strip(),
                recipient_email=item["email"].strip().lower(),
                certificate_number=f"CERT-{job.id.hex[:10].upper()}-{index:04d}",
            )
            for index, item in enumerate(recipients, start=1)
        ]
        Certificate.objects.bulk_create(certificate_rows)
        return job


class CertificateSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            "id", "recipient_name", "recipient_email", "certificate_number",
            "status", "file", "download_url", "error_message", "created_at", "completed_at"
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class GenerationJobSerializer(serializers.ModelSerializer):
    progress_percent = serializers.FloatField(read_only=True)
    certificates = CertificateSerializer(many=True, read_only=True)

    class Meta:
        model = GenerationJob
        fields = [
            "id", "event_name", "certificate_title", "event_date", "issuer_name",
            "issuer_title", "status", "total_recipients", "processed_count",
            "successful_count", "failed_count", "progress_percent", "error_message",
            "created_at", "started_at", "completed_at", "certificates"
        ]
        read_only_fields = fields
