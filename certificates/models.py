import uuid
from django.core.validators import EmailValidator
from django.db import models


class GenerationJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS", "Completed with errors"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(max_length=200)
    certificate_title = models.CharField(max_length=200, default="Certificate of Participation")
    event_date = models.DateField(null=True, blank=True)
    issuer_name = models.CharField(max_length=150)
    issuer_title = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    total_recipients = models.PositiveIntegerField(default=0)
    processed_count = models.PositiveIntegerField(default=0)
    successful_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def progress_percent(self):
        if not self.total_recipients:
            return 0
        return round((self.processed_count / self.total_recipients) * 100, 2)

    def __str__(self):
        return f"{self.event_name} ({self.id})"


class Certificate(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(GenerationJob, on_delete=models.CASCADE, related_name="certificates")
    recipient_name = models.CharField(max_length=150)
    recipient_email = models.EmailField(validators=[EmailValidator()])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    certificate_number = models.CharField(max_length=100, unique=True)
    file = models.FileField(upload_to="certificates/%Y/%m/%d/", blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "recipient_email"],
                name="unique_recipient_per_job",
            )
        ]

    def __str__(self):
        return f"{self.recipient_name} - {self.certificate_number}"
