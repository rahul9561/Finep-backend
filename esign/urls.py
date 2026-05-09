# urls.py
from django.urls import path
from .views import *

urlpatterns = [ 
 
  path(
        "leegality/create-sign/",
        CreateLeegalitySignAPIView.as_view()
    ),

    path(
        "leegality/document-details/",
        FetchLeegalityDocumentAPIView.as_view()
    ),
]