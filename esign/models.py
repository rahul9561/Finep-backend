from django.db import models
from django.conf import settings


class LeegalityDocument(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SIGNED", "Signed"),
        ("FAILED", "Failed"),
        ("EXPIRED", "Expired"),
    )

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="esign_reports"
    )

    profile_id = models.CharField(
        max_length=255
    )

    document_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )

    irn = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    cost_price = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    reference_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    raw_response = models.JSONField(
        null=True,
        blank=True
    )

    signer_name = models.CharField(
        max_length=255
    )

    signer_email = models.EmailField()

    signer_phone = models.CharField(
        max_length=20
    )

    file_name = models.CharField(
        max_length=255
    )

    sign_url = models.TextField(
        null=True,
        blank=True
    )

    signed_pdf_url = models.TextField(
        null=True,
        blank=True
    )

    audit_trail_url = models.TextField(
        null=True,
        blank=True
    )

    used_signature_type = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    invitation_status = models.CharField(
        max_length=255,
        default="PENDING"
    )

    completion_date = models.DateTimeField(
        null=True,
        blank=True
    )

    webhook_payload = models.JSONField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.document_id} - {self.status}"