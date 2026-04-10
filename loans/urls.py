

from django.urls import path

from .views import *

urlpatterns = [

    path("categories/", CategoryAPIView.as_view()),

    path("banks/", BanksAPIView.as_view()),
    path("journey/",JourneyAPIView.as_view()),

    path("apply/", CreateLoanAPIView.as_view()),
    path("salary-check/", SalaryCheckAPIView.as_view()),
    
    path("svatantr/sync/",SvatantrSyncAPIView.as_view()),

    path("svatantr/list/", LoanListAPIView.as_view()),
    path("admin/svatantr/list/",AdminLoanListAPIView.as_view()),
    path("svatantr/mis/", MISAPIView.as_view()),
    
    # propelld
    path(
        "propelld/apply/",
        ApplyPropelldLoanAPIView.as_view(),
    ),
     path(
        "propelld/emi/",
        EmiAPIView.as_view(),
    ),
     
     
    path("propelld/approvequote/",ApproveQuoteAPIView.as_view()),

    path(
        "propelld/webhook/",
        PropelldWebhookAPIView.as_view()
    ),
    path(
    "propelld/status/<int:loan_id>/",
    PropelldLoanStatusAPIView.as_view(),
),
]

