# loans/models.py
from django.db import models
from django.core.validators import RegexValidator



class LoanApplication(models.Model):

    STATUS_CHOICES = [
        ("CREATED", "Created"),
        ("QUOTE_CREATED", "Quote Created"),
        ("APPLIED", "Applied"),
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("DISBURSED", "Disbursed"),
    ]

    # Agent
    agent = models.ForeignKey(
        "agent.Agent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loans"
    )

    # Customer
    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="loans"
    )

    # Basic Info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)

    email = models.EmailField()
    mobile = models.CharField(max_length=15)

    # Loan info
    loan_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discounted_course_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    moratorium = models.IntegerField(default=0)

    course_id = models.IntegerField()

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Propelld data
    propelld_quote_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    propelld_application_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="CREATED"
    )

    response_data = models.JSONField(
        null=True,
        blank=True
    )

    notes = models.JSONField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.id} - {self.loan_amount}"
   
   
class PropelldWebhookLog(models.Model):

    event = models.CharField(max_length=100)

    application_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    payload = models.JSONField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.event
  
    
class LoanStatusHistory(models.Model):

    loan = models.ForeignKey(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name="history"
    )

    status = models.CharField(max_length=50)

    data = models.JSONField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    ) 


def loan_document_upload_path(instance, filename):
    return (
        f"loan_documents/"
        f"{instance.application.public_id}/"
        f"{instance.document_type.code}/"
        f"{filename}"
    )







import uuid
from django.conf import settings

    
# new code for loan   
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class LoanLead(models.Model):

    STATUS = (
        ("CREATED", "CREATED"),
        ("SENT", "SENT"),
        ("PROCESSING", "PROCESSING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
        ("SANCTIONED", "SANCTIONED"),
        ("DISBURSED", "DISBURSED"),
        ("FAILED", "FAILED"),
    )

    # -----------------------
    # BASIC
    # -----------------------

    name = models.CharField(max_length=200)

    mobile = models.CharField(max_length=15)

    pincode = models.CharField(max_length=10)

    # -----------------------
    # PROVIDER
    # -----------------------

    provider_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    provider_lead_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        db_index=True
    )

    category_id = models.CharField(max_length=200)

    category_code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    bank_id = models.CharField(max_length=200)

    bank_name = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    application_no = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    # -----------------------
    # AMOUNT
    # -----------------------

    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    approved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    disbursed_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    existing_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # -----------------------
    # USER / AGENT
    # -----------------------

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_leads"
    )

    agent = models.ForeignKey(
        "agent.Agent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads"
    )

    # -----------------------
    # STATUS
    # -----------------------

    status = models.CharField(
        max_length=50,
        choices=STATUS,
        default="CREATED"
    )

    status_message = models.TextField(
        null=True,
        blank=True
    )

    telecaller_status = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    is_complete = models.BooleanField(
        default=False
    )

    # -----------------------
    # RESPONSE
    # -----------------------

    provider_response = models.JSONField(
        null=True,
        blank=True
    )

    redirect_url = models.URLField(
        max_length=2000,
        null=True,
        blank=True
    )

    # -----------------------
    # TRACKING
    # -----------------------

    utm_source = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    utm_campaign = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    # -----------------------
    # TIME
    # -----------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # -----------------------

    def __str__(self):
        return f"{self.name} - {self.mobile} - {self.status}"
    
    
class SyncLog(models.Model):

    SERVICE_CHOICES = (
        ("SVATANTR", "Svatantr"),
    )

    service = models.CharField(
        max_length=50,
        choices=SERVICE_CHOICES,
    )

    total = models.IntegerField(default=0)

    updated = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        default="SUCCESS"
    )

    message = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.service} - {self.total}"