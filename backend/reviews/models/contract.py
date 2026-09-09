from django.conf import settings
from django.db import models


class Contract(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETE = "COMPLETE", "Complete"
        FAILED = "FAILED", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contracts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Null for contracts created outside the API (eval harness, management commands).",
    )
    filename = models.CharField(max_length=255, blank=True)
    source_text = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.filename or f"Contract #{self.pk}"
