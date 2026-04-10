from django.urls import path
from .views import *

urlpatterns = [
    path("all/balace/summary/",DashboardSummaryAPIView.as_view()),
    path("agent/dashboard/summary/", AgentDashboardAPIView.as_view()),
    path("agent/recent/transactions/", RecentTransactionsAPIView.as_view()),
    path("customer/dashboard/", CustomerDashboardView.as_view()),
    path("agent/customer-transactions/", AgentCustomerTransactionsView.as_view()),
]
