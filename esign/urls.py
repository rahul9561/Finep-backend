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
    
    path(
        "leegality/download/<str:document_id>/",
        DownloadSignedPDFAPIView.as_view()
    ),
    

    path("leegality/webhook/",leegality_webhook,name="leegality_webhook")
]