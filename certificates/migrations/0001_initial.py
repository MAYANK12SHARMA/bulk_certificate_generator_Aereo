# Generated manually to keep the project self-contained in the deliverable.
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GenerationJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_name", models.CharField(max_length=200)),
                ("certificate_title", models.CharField(default="Certificate of Participation", max_length=200)),
                ("event_date", models.DateField(blank=True, null=True)),
                ("issuer_name", models.CharField(max_length=150)),
                ("issuer_title", models.CharField(blank=True, max_length=150)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("PROCESSING", "Processing"), ("COMPLETED", "Completed"), ("COMPLETED_WITH_ERRORS", "Completed with errors"), ("FAILED", "Failed")], default="PENDING", max_length=30)),
                ("total_recipients", models.PositiveIntegerField(default=0)),
                ("processed_count", models.PositiveIntegerField(default=0)),
                ("successful_count", models.PositiveIntegerField(default=0)),
                ("failed_count", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Certificate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("recipient_name", models.CharField(max_length=150)),
                ("recipient_email", models.EmailField(max_length=254, validators=[django.core.validators.EmailValidator()])),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("PROCESSING", "Processing"), ("COMPLETED", "Completed"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("certificate_number", models.CharField(max_length=100, unique=True)),
                ("file", models.FileField(blank=True, upload_to="certificates/%Y/%m/%d/")),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="certificates", to="certificates.generationjob")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="certificate",
            constraint=models.UniqueConstraint(fields=("job", "recipient_email"), name="unique_recipient_per_job"),
        ),
    ]
