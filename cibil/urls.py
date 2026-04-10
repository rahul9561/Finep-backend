from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_admin import (
    AdminPrefillView,
    AdminGenerateReportView,
    
)

router = DefaultRouter()

router.register("admin/recharge-plans", AdminRechargePlanViewSet, basename="admin-recharge-plans")

urlpatterns = [
    path("purchase-recharge-plan/",PurchaseRechargePlanAPIView.as_view()),
    path("recharge-plans/", RechargePlanAPIView.as_view()),
    path("prefill-mobile/", prefill_mobile),
    path("generate-report/", GenerateCibilReportView.as_view()),
    path("agent/cibil-stats/", AgentCibilStatsAPIView.as_view()),
    path("history/",AgentCibilReportHistoryAPIView.as_view()),
    path("analytics/",AgentReportAnalyticsAPIView.as_view()),
    path("usage/", AgentServiceUsageAPIView.as_view()),
    path("download-all/", DownloadAllReportsAPIView.as_view()),
    path("download-reports/", DownloadReportsByDateAPIView.as_view()),
    path(
        "agent/active-plan/",
        AgentActivePlanView.as_view(),
        name="agent-active-plan",
    ),
    path(
    "download-reports-range/",
    DownloadReportsByRangeAPIView.as_view(),
    ),
    path("admin/CibilReportList/",AdminCibilReportListAPIView.as_view()),

    # urls.py

    path(
        "admin/report-stats/",
        AdminUserReportStatsAPIView.as_view()
    ),
    
    path(
        "prefill-check/",
        prefill_check
    ),

    path(
        "generate-report/v1/",
        GenerateReportAfterPrefillView.as_view()
    ),
    
    path(
        "set-pricing/",
        SetCibilPricingView.as_view()
    ),
    
    path("customer-pricing/",CustomerPricingAPIView.as_view(), name="customer-pricing"),
    
    
     path(
        "admin/prefill/",
        AdminPrefillView.as_view()
    ),

    path(
        "admin/generate/",
        AdminGenerateReportView.as_view()
    ),

    path("", include(router.urls)),
]

