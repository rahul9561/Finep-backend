# urls.py

from django.urls import path
from .views import Mobile360APIView


urlpatterns = [
    path(
        "mobile360/check/",
        Mobile360APIView.as_view(),
        name="mobile360-api"
    ),
]