from django.urls import path
from .views import main_balance_view, cash_balance_view

urlpatterns = [
    path("balance/main/", main_balance_view),
    path("balance/cash/", cash_balance_view),
]