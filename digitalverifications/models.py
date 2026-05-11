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
        related_name="mobile360_logs",
        null=True,
        blank=True
    )

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_mobile360_logs",
        null=True,
        blank=True
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_mobile360_logs",
        null=True,
        blank=True
    )

    mobile = models.CharField(max_length=15)

    txn_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    reference_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
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