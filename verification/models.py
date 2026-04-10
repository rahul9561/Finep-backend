from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class BankVerificationReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    id_number = models.CharField(max_length=50)
    ifsc = models.CharField(max_length=20)
    status = models.BooleanField(default=False)   # ✅ ADD

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)


class PanVerificationReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    pan_number = models.CharField(max_length=20)
    status = models.BooleanField(default=False)   # ✅ ADD

    full_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    dob = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)


class AadhaarValidationReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    aadhaar_number = models.CharField(max_length=20)
    status = models.BooleanField(default=False)   # ✅ ADD

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    
    
class GSTReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    gst_number = models.CharField(max_length=50)
    status = models.BooleanField(default=False)   # ✅ ADD

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)


class MSMEReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    pan = models.CharField(max_length=20)
    status = models.BooleanField(default=False)   # ✅ ADD

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)


class RCReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rc_number = models.CharField(max_length=50)
    status = models.BooleanField(default=False)   # ✅ ADD

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)


class ElectricityReport(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    id_number = models.CharField(max_length=100)
    status = models.BooleanField(default=False)   # ✅ ADD

    operator_code = models.CharField(max_length=20)

    response = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
# models.py

class APIPricing(models.Model):

    SERVICE_CHOICES = [
        ("pan", "PAN"),
        ("aadhaar", "Aadhaar"),
        ("gst", "GST"),
        ("msme", "MSME"),
        ("rc", "RC"),
        ("electricity", "Electricity"),
    ]

    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_prices"
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="customer_prices"
    )

    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["agent", "customer", "service"]

    # 🔥 ADD HERE
    def save(self, *args, **kwargs):
        if self.customer == self.agent:
            raise ValueError("Agent cannot be customer")
        super().save(*args, **kwargs)