from django.urls import path
from .views import create_order, cashfree_webhook

urlpatterns = [
    path("create-cashfree-order/", create_order),
    path("cashfree/webhook/", cashfree_webhook),
]