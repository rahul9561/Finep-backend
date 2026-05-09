from django.shortcuts import render
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import LeegalityDocument

from .services.leegality_service import (
    LeegalityService
)


# =====================================
# CREATE SIGN REQUEST
# =====================================

# CREATE SIGN REQUEST VIEW
from django.conf import settings

class CreateLeegalitySignAPIView(APIView):

    def post(self, request):

        pdf_file = request.FILES.get("file")

        if not pdf_file:

            return Response(
                {
                    "error": "PDF file required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        signer_name = request.data.get("name")

        signer_email = request.data.get("email")

        signer_phone = request.data.get("phone")

        irn = request.data.get(
            "irn",
            "ORDER_1001"
        )

        # PDF -> Base64
        base64_pdf = base64.b64encode(
            pdf_file.read()
        ).decode("utf-8")

        service = LeegalityService()

        response = service.create_sign_request(

            file_name=pdf_file.name,

            base64_file=base64_pdf,

            signer_name=signer_name,

            signer_email=signer_email,

            signer_phone=signer_phone,

            irn=irn
        )

        print(response)

        # MAIN DATA
        # data = response.get("data", {})
        data = response.get("data", {}).get("data", {})

        # DOCUMENT ID
        document_id = data.get(
            "documentId"
        )

        if not document_id:

            return Response(
                {
                    "success": False,
                    "message": "Document creation failed",
                    "response": response
                },
                status=400
            )

        # INVITEES
        invitees = data.get(
            "invitees",
            []
        )

        sign_url = None

        expiry_date = None

        if invitees:

            sign_url = invitees[0].get(
                "signUrl"
            )

            expiry_date = invitees[0].get(
                "expiryDate"
            )

        # SAVE DB
        leegality_doc = (
            LeegalityDocument.objects.create(

                profile_id=settings.LEEGALITY_PROFILE_ID,

                document_id=document_id,

                irn=irn,

                signer_name=signer_name,

                signer_email=signer_email,

                signer_phone=signer_phone,

                file_name=pdf_file.name,

                sign_url=sign_url,

                status="PENDING"
            )
        )

        return Response({

            "success": True,

            "message": "Sign request created successfully",

            "document_id": document_id,

            "sign_url": sign_url,

            "expiry_date": expiry_date,

            "response": response
        })


# =====================================
# FETCH DOCUMENT DETAILS
# =====================================
class FetchLeegalityDocumentAPIView(APIView):

    def get(self, request):

        document_id = request.GET.get(
            "document_id"
        )

        if not document_id:

            return Response(
                {
                    "error": "document_id required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        service = LeegalityService()

        response = service.fetch_document_details(
            document_id=document_id
        )

        print(response)

        # =========================
        # ACTUAL API DATA
        # =========================

        data = response.get(
            "data",
            {}
        ).get(
            "data",
            {}
        )

        # =========================
        # INVITEES
        # =========================

        invitees = data.get(
            "invitees",
            []
        )

        invitee_data = {}

        if invitees:

            invitee_data = invitees[0]

        # =========================
        # EXTRACT DATA
        # =========================

        sign_url = invitee_data.get(
            "signUrl"
        )

        expiry_date = invitee_data.get(
            "expiryDate"
        )

        signer_name = invitee_data.get(
            "name"
        )

        signer_email = invitee_data.get(
            "email"
        )

        signer_phone = invitee_data.get(
            "phone"
        )

        active = invitee_data.get(
            "active",
            False
        )

        completion_date = data.get(
            "completionDate"
        )

        used_signature_type = data.get(
            "usedSignatureType"
        )

        # =========================
        # STATUS
        # =========================

        document_status = (
            "SIGNED"
            if completion_date
            else "PENDING"
        )

        # =========================
        # UPDATE DATABASE
        # =========================

        try:

            leegality_doc = (
                LeegalityDocument.objects.get(
                    document_id=document_id
                )
            )

            leegality_doc.sign_url = (
                sign_url
            )

            leegality_doc.used_signature_type = (
                used_signature_type
            )

            leegality_doc.completion_date = (
                completion_date
            )

            leegality_doc.invitation_status = (
                "ACTIVE"
                if active
                else "INACTIVE"
            )

            leegality_doc.status = (
                document_status
            )

            leegality_doc.save()

        except LeegalityDocument.DoesNotExist:

            return Response(
                {
                    "error": "Document not found in DB"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =========================
        # FINAL RESPONSE
        # =========================

        return Response({

            "success": True,

            "document_id": document_id,

            "status": document_status,

            "sign_url": sign_url,

            "expiry_date": expiry_date,

            "completion_date": completion_date,

            "signer_name": signer_name,

            "signer_email": signer_email,

            "signer_phone": signer_phone,

            "response": response
        })