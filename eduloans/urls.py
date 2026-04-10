from django.urls import path
from .views import *

urlpatterns = [

    # ---------------- CIBIL ----------------

    path(
        "educations/student-cibil/",
        StudentCibilCheckView.as_view()
    ),

    path(
        "coapplicant-cibil-check/",
        CoApplicantCibilCheckView.as_view(),
    ),

    # ---------------- BANK ----------------

    path(
        "coapplicant/bank/check/",
        CoApplicantBankCheckView.as_view(),
    ),

    # ---------------- PAN ----------------

    path(
        "verify/pan/",
        PanVerifyView.as_view(),
    ),

    # ---------------- AADHAAR ----------------

    path(
        "verify/aadhaar/",
        AadhaarVerifyView.as_view(),
    ),

    # ---------------- MSME ----------------

    path(
        "verify/msme/",
        MSMEVerifyView.as_view(),
    ),

    # ---------------- GST ----------------

    path(
        "verify/gst/",
        GSTVerifyView.as_view(),
    ),

    # ---------------- ITR ----------------

    path(
        "verify/itr/",
        ITRVerifyView.as_view(),
    ),
    
    # ---------------- DigiLockerEducationCheck ----------------
    
    
    path(
    "educations/digilocker-check/",
    DigiLockerEducationCheck.as_view(),
    ),
    
    #----------------DeathVerifyAPIView-----------------
    path("death/verify/",DeathVerifyAPIView.as_view()),

    # ---------------- APPLY ----------------

    path(
        "apply/",
        EducationLoanApplyView.as_view(),
        name="education-apply",
    ),

    # ---------------- ADMIN ----------------

    path(
        "admin/education-loans/",
        AdminEducationLoanListAPIView.as_view(),
    ),

]