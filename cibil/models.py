import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class CibilReport(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )
    REPORT_TYPES = (
        ("cibil", "CIBIL"),
        ("experian", "Experian"),
        ("equifax", "Equifax"),
        ("crif", "CRIF"),
        ('prefill', 'Prefill'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cibil_reports"
    )

    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)
    pan = models.CharField(max_length=15, db_index=True)
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        null=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    response_message = models.TextField(blank=True, null=True)

    report_pdf = models.FileField(upload_to="cibil_reports/", max_length=1000, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)



    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["pan"]),
            models.Index(fields=["agent", "created_at"]),
        ]



class RechargePlan(models.Model):

    PLAN_TYPE = (
        ("FIXED", "Fixed"),
        ("RANGE", "Range"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE)

    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    min_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    prefill_price = models.DecimalField(max_digits=10, decimal_places=2)
    cibil_price = models.DecimalField(max_digits=10, decimal_places=2)
    crif_price = models.DecimalField(max_digits=10, decimal_places=2)
    equifax_price = models.DecimalField(max_digits=10, decimal_places=2)
    experian_price = models.DecimalField(max_digits=10, decimal_places=2)
    aadhaar_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pan_verify_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_verify_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bank_verify_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    cibil_commercial = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"{self.title} - ₹{self.amount}"
    def __str__(self):
        return f"{self.title} ({self.plan_type})"


# cibil/models.py

class AgentPlan(models.Model):

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_cibil_plans"
    )

    plan = models.ForeignKey(
        RechargePlan,
        on_delete=models.CASCADE
    )

    remaining_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agent} - {self.plan.title}"


class PlanUsage(models.Model):

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plan_usages"
    )

    report = models.ForeignKey(
        CibilReport,
        on_delete=models.CASCADE,
        related_name="usages",
        null=True,
        blank=True
    )
    # ✅ ADD THIS
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_usages"
    )

    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    service = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="PENDING")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2,null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    reference_id = models.CharField(
            max_length=50,
            unique=True,
            null=True,
            blank=True
        )

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["agent", "service"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.agent} - {self.service} - ₹{self.price}"

    
    
    
class AgentCibilPricing(models.Model):

    SERVICE_CHOICES = [
        ("cibil", "CIBIL"),
        ("experian", "Experian"),
        ("equifax", "Equifax"),
        ("crif", "CRIF"),
        ("prefill", "Prefill"),
        ("aadhaar_verify", "Aadhaar Verify"), 
        ("pan_verify", "PAN Verify"),
        ("gst_verify", "GST Verify"),
        ("bank_verify", "Bank Verify"),
    ]

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cibil_prices"   # ✅ FIX
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="customer_cibil_prices"   # ✅ FIX
    )

    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

        
    class Meta:
        unique_together = ["agent", "customer", "service"]
        indexes = [
            models.Index(fields=["agent", "service"]),
            models.Index(fields=["customer"]),
        ]