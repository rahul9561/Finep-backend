import uuid
from django.db import models
from agent.models import Agent
from .utils import education_upload_path

# -----------------------------
# Telecaller
# -----------------------------
class TeleCaller(models.Model):

    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name


# -----------------------------
# Main Application
# -----------------------------
class EducationLoanApplication(models.Model):
    GENDER = (
        ("male", "Male"),
        ("female", "Female"),
    )

    MARITAL = (
        ("single", "Single"),
        ("married", "Married"),
    )

    CO_TYPE = (
        ("none", "No Co-applicant"),
        ("business", "Business"),
        ("agriculture", "Agriculture"),
        ("salaried", "Salaried"),
        ("pension", "Pension"),
        ("others", "Others"),
    )
    LOAN_TYPE = (
        ("domestic", "Domestic"),
        ("abroad", "Abroad"),
    )

    loan_type = models.CharField(
        max_length=20,
        choices=LOAN_TYPE,
        default="domestic"
    )


    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="education_loans"
    )

    name = models.CharField(max_length=200)

    country = models.CharField(max_length=200,blank=True, null=True)

    course = models.CharField(max_length=200,blank=True, null=True)

    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    sale_executive = models.CharField(
        max_length=200,
        blank=True
    )

    telecaller = models.ForeignKey(
        TeleCaller,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    gender = models.CharField(max_length=10, choices=GENDER)

    marital_status = models.CharField(max_length=10, choices=MARITAL)

    co_applicant_type = models.CharField(
        max_length=20,
        choices=CO_TYPE,
        default="none"
        )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class StudentDetails(models.Model):
    
    application = models.OneToOneField(
        "EducationLoanApplication",
        on_delete=models.CASCADE,
        related_name="student"
    )

    # ✅ uploads
    photo = models.ImageField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    aadhaar_front = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    aadhaar_back = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ---------- PAN ----------

    pan_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    pan = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )


    passport = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    study_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    offer_letter = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    experience_letter = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    address_proof = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    mother_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    father_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ✅ text fields
    score = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    grandmother = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    granny = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ref1 = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    ref2 = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    cibil_score = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.application)
    
    
    
    
    

class CoApplicant(models.Model):

    CO_TYPE = (
        ("business", "Business"),
        ("agriculture", "Agriculture"),
        ("salaried", "Salaried"),
        ("pension", "Pension"),
        ("others", "Others"),
    )

    application = models.OneToOneField(
        "EducationLoanApplication",
        on_delete=models.CASCADE,
        related_name="coapplicant"
    )

    type = models.CharField(
        max_length=20,
        choices=CO_TYPE,
        blank=True,
        null=True
    )

    # ---------- BASIC ----------

    photo = models.ImageField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    aadhaar_front = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    aadhaar_back = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    pan = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    pan_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    cibil_score = models.IntegerField(
        blank=True,
        null=True
    )

    # ---------- COMMON DOCS ----------

    bank_statement = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    itr = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ---------- SALARIED ----------

    salary_slip = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ---------- AGRICULTURE ----------

    land_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    income_certificate = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ---------- PENSION ----------

    ppo = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ---------- BUSINESS ----------

    gst = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    business_photos = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    business_address_proof = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    business_address = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    office_address = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return str(self.application)
    
    
class CoApplicantBankCheck(models.Model):

    application = models.OneToOneField(
        "EducationLoanApplication",
        on_delete=models.CASCADE,
        related_name="bank_check"
    )

    file = models.FileField(
        upload_to="bank_statements/"
    )

    is_verified = models.BooleanField(
        default=False
    )

    message = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return str(self.application)
    
#  only female married  
    
class HusbandDetails(models.Model):

    application = models.OneToOneField(
        "EducationLoanApplication",
        on_delete=models.CASCADE,
        related_name="husband"
    )

    husband_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    father_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    mother_docs = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    marriage_certificate = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    address_proof = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return str(self.application)
    



class PropertyDetails(models.Model):

    application = models.OneToOneField(
        "EducationLoanApplication",
        on_delete=models.CASCADE,
        related_name="property"
    )

    # ✅ property documents upload
    documents = models.FileField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    owner_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    owner_father = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # ✅ property photos upload
    photos = models.ImageField(
        upload_to=education_upload_path,
        blank=True,
        null=True
    )

    # ✅ yes / no
    loan_on_property = models.BooleanField(
        default=False
    )

    loan_details = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # ✅ numeric
    area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    valuation = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    LOCATION_TYPE = (
        ("domestic", "Domestic"),
        ("commercial", "Commercial"),
        ("rural", "Rural"),
        ("city", "City"),
    )

    location = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE,
        blank=True,
        null=True
    )

    remark = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    
    def __str__(self):
      return f"{self.application.name} property"
  
  
  
  
  

    
class SurepassLog(models.Model):

    application = models.ForeignKey(
        "EducationLoanApplication",
        on_delete=models.CASCADE
    )

    service = models.CharField(
        max_length=50
    )  
    # cibil / bank / pan / itr

    request_data = models.JSONField()

    response_data = models.JSONField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=50,
        default="pending"
    )

    reference_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    
    
class VerificationStatus(models.Model):

    application = models.OneToOneField(
        "EducationLoanApplication",
        on_delete=models.CASCADE,
        related_name="verification"
    )

    student_cibil = models.BooleanField(default=False)
    co_cibil = models.BooleanField(default=False)

    bank_verified = models.BooleanField(default=False)

    pan_verified = models.BooleanField(default=False)
    aadhaar_verified = models.BooleanField(default=False)

    itr_verified = models.BooleanField(default=False)

    msme_verified = models.BooleanField(default=False)
    gst_verified = models.BooleanField(default=False)

    consent_verified = models.BooleanField(default=False)
    
    education_verified = models.BooleanField(
        default=False
    )
    

    final_status = models.CharField(
        max_length=50,
        default="pending"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)