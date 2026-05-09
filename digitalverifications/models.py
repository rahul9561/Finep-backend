# models.py

from django.db import models
from django.conf import settings


class Mobile360Log(models.Model):

    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mobile360_logs"
    )

    mobile = models.CharField(max_length=15)

    txn_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    message = models.TextField(
        blank=True,
        null=True
    )

    response_data = models.JSONField(
        blank=True,
        null=True
    )

    raw_response = models.JSONField(
        blank=True,
        null=True
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
        return f"{self.mobile} - {self.status}"