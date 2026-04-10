from django.urls import path
from .views import *

urlpatterns = [

    path("bank/", BankVerificationView.as_view()),
    path("pan/", PanVerifyView.as_view()),
    path("aadhaar/", AadhaarValidationView.as_view()),
    path("gst/", GSTView.as_view()),
    path("msme/", MSMEView.as_view()),
    path("rc/", RCView.as_view()),
    path("electricity/", ElectricityView.as_view()),
    
    # admin access
    
    path(
        "admin/dashboard/",
        AdminDashboardView.as_view(),
    ),
    path("admin/activity/",AdminActivityView.as_view()),
    path("agent/reports/", AgentCustomerReportsView.as_view()),
    path("agent/transactions/", AgentCustomerTransactionsView.as_view()),
    path("set/pricing/", SetAPIPricingView.as_view()),
    path("get/pricing/", GetMyPricingView.as_view()),
    
    path("customer/report-history/", CustomerReportHistoryView.as_view()),

]

