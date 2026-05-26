# views.py
from django.shortcuts import render
import base64
from cibil.models import PlanUsage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import (
    MultiPartParser,
    FormParser
)
from django.conf import settings
from django.db import transaction
from django.db.models import Sum

from decimal import Decimal
import uuid

from wallet.models import Wallet
from wallet.services import (
    wallet_debit,
    wallet_credit
)

from cibil.models import (
    AgentPlan,
    AgentCibilPricing
)

from .models import LeegalityDocument

from .services.leegality_service import (
    LeegalityService
)


# =====================================================
# GET SELLING PRICE
# =====================================================
def get_leegality_price(user):

    if hasattr(user, "created_by") and user.created_by:
        agent = user.created_by
        customer = user
    else:
        agent = user
        customer = None

    # CUSTOMER CUSTOM PRICE
    if customer:

        custom = AgentCibilPricing.objects.filter(
            agent=agent,
            customer=customer,
            service="leegality_esign"
        ).order_by("-id").first()

        if custom:
            return custom.price

    # AGENT DEFAULT PRICE
    agent_price = AgentCibilPricing.objects.filter(
        agent=agent,
        customer__isnull=True,
        service="leegality_esign"
    ).order_by("-id").first()

    if agent_price:
        return agent_price.price

    # FALLBACK PLAN PRICE
    plan = AgentPlan.objects.filter(
        agent=agent,
        is_active=True
    ).last()

    if plan:
        return plan.plan.leegality_esign_price

    return 0


# =====================================================
# CREATE SIGN REQUEST
# =====================================================
class CreateLeegalitySignAPIView(APIView):
    
    parser_classes = (
        MultiPartParser,
        FormParser
    )

    @transaction.atomic
    def post(self, request):

        user = request.user

        # =====================================
        # USER IDENTIFY
        # =====================================
        if hasattr(user, "created_by") and user.created_by:
            customer = user
            agent = user.created_by
        else:
            customer = None
            agent = user

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
        
        if not signer_name or not signer_email or not signer_phone:

            return Response(
                {
                    "success": False,
                    "message": "Name, email and phone are required"
                },
                status=400
            )

        # irn = request.data.get(
        #     "irn",
        #     "ORDER_1001"
        # )
        irn = f"ESIGN-{uuid.uuid4().hex[:10]}"

        # =====================================
        # PLAN CHECK
        # =====================================
        agent_plan = AgentPlan.objects.select_for_update().filter(
            agent=agent,
            is_active=True
        ).order_by("created_at")

        if not agent_plan.exists():

            return Response(
                {
                    "success": False,
                    "message": "Please recharge plan"
                },
                status=400
            )

        active_plan = agent_plan.last()

        # =====================================
        # COST PRICE
        # =====================================
        cost_price = active_plan.plan.leegality_esign_price

        if not cost_price or cost_price <= 0:

            return Response(
                {
                    "success": False,
                    "message": "Leegality price not configured"
                },
                status=400
            )

        # =====================================
        # SELLING PRICE
        # =====================================
        selling_price = get_leegality_price(user)

        # =====================================
        # BALANCE CHECK
        # =====================================
        total_balance = agent_plan.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        if total_balance < cost_price:

            return Response(
                {
                    "success": False,
                    "message": "Insufficient balance"
                },
                status=400
            )

        # =====================================
        # CUSTOMER WALLET CHECK
        # =====================================
        if customer:

            wallet = Wallet.objects.filter(
                user=customer
            ).first()

            if not wallet or wallet.balance < selling_price:

                return Response(
                    {
                        "success": False,
                        "message": "Insufficient wallet balance"
                    },
                    status=400
                )

            # CUSTOMER DEBIT
            wallet_debit(
                user=customer,
                amount=selling_price,
                service="leegality_esign",
                note="Leegality Aadhaar eSign"
            )

        # =====================================
        # PDF -> BASE64
        # =====================================
        base64_pdf = base64.b64encode(
            pdf_file.read()
        ).decode("utf-8")

        # =====================================
        # API CALL
        # =====================================
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

        data = response.get(
            "data",
            {}
        ).get(
            "data",
            {}
        )

        # =====================================
        # FAILED => REFUND
        # =====================================
        if response.get("status_code") != 200:
            

            if customer:

                wallet_credit(
                    user=customer,
                    amount=selling_price,
                    service="leegality_esign",
                    note="Refund Aadhaar eSign failed"
                )
                
            PlanUsage.objects.create(

                agent=agent,

                customer=customer if customer else None,

                service="leegality_esign",

                status="FAILED",

                cost_price=cost_price,

                price=selling_price,

                profit=0,

                reference_id=f"LEEGFAIL-{uuid.uuid4().hex[:10]}"
            )

            return Response(
                {
                    "success": False,
                    "message": "Document creation failed",
                    "response": response
                },
                status=400
            )

        # =====================================
        # DOCUMENT ID
        # =====================================
        document_id = data.get(
            "documentId"
        )

        if not document_id:

            if customer:

                wallet_credit(
                    user=customer,
                    amount=selling_price,
                    service="leegality_esign",
                    note="Refund Aadhaar eSign failed"
                )
            # =====================================
            # SAVE FAILED USAGE
            # =====================================

            PlanUsage.objects.create(

                agent=agent,

                customer=customer if customer else None,

                service="leegality_esign",

                status="FAILED",

                cost_price=cost_price,

                price=selling_price,

                profit=0,

                reference_id=f"LEEGFAIL-{uuid.uuid4().hex[:10]}"
            )

            return Response(
                {
                    "success": False,
                    "message": "Document creation failed",
                    "response": response
                },
                status=400
            )

        # =====================================
        # AGENT BALANCE DEDUCT
        # =====================================
        remaining_price = Decimal(cost_price)

        for p in agent_plan:

            if p.remaining_balance >= remaining_price:

                p.remaining_balance -= remaining_price

                if p.remaining_balance == 0:
                    p.is_active = False

                p.save()

                break

            else:

                remaining_price -= p.remaining_balance

                p.remaining_balance = 0

                p.is_active = False

                p.save()

        # =====================================
        # INVITEES
        # =====================================
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

        # =====================================
        # PROFIT
        # =====================================
        profit = max(
            Decimal(selling_price) - Decimal(cost_price),
            0
        )
        
        
        # =====================================
        # SAVE USAGE HISTORY
        # =====================================


        PlanUsage.objects.create(

            agent=agent,

            customer=customer if customer else None,

            service="leegality_esign",

            status="SUCCESS",

            cost_price=cost_price,

            price=selling_price,

            profit=profit,

            reference_id=f"LEEG-{uuid.uuid4().hex[:10]}"
        )

        # =====================================
        # SAVE DB
        # =====================================
        leegality_doc = (
            LeegalityDocument.objects.create(

                agent=agent,

                profile_id=settings.LEEGALITY_PROFILE_ID,

                document_id=document_id,

                irn=irn,

                signer_name=signer_name,

                signer_email=signer_email,

                signer_phone=signer_phone,

                file_name=pdf_file.name,

                sign_url=sign_url,

                status="PENDING",

                cost_price=cost_price,

                selling_price=selling_price,

                profit=profit,

                reference_id=f"ESIGN-{uuid.uuid4().hex[:10]}",

                raw_response=data
            )
        )

        return Response({

            "success": True,

            "message": "Sign request created successfully",

            "document_id": document_id,

            "sign_url": sign_url,

            "expiry_date": expiry_date,

            "cost_price": cost_price,

            "selling_price": selling_price,

            "profit": profit,

            "response": response
        })


# =====================================
# FETCH DOCUMENT DETAILS
# =====================================
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
                    "success": False,
                    "message": "document_id required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================
        # FETCH FROM DATABASE
        # =====================================

        try:

            leegality_doc = (
                LeegalityDocument.objects.get(
                    document_id=document_id
                )
            )

        except LeegalityDocument.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Document not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =====================================
        # OPTIONAL:
        # FETCH LATEST DATA FROM LEEGALITY
        # =====================================

        service = LeegalityService()

        response = service.fetch_document_details(
            document_id=document_id
        )

        print("FETCH RESPONSE")
        print(response)

        data = response.get(
            "data",
            {}
        ).get(
            "data",
            {}
        )

        invitees = data.get(
            "invitees",
            []
        )

        invitee_data = {}

        if invitees:
            invitee_data = invitees[0]

        # =====================================
        # UPDATE OPTIONAL DETAILS ONLY
        # DO NOT OVERWRITE STATUS
        # =====================================
        
        

        sign_url = (
            invitee_data.get("signUrl")
            or leegality_doc.sign_url
        )

        completion_date = (
            data.get("completionDate")
            or leegality_doc.completion_date
        )

        used_signature_type = (
            data.get("usedSignatureType")
            or leegality_doc.used_signature_type
        )

        active = invitee_data.get(
            "active",
            False
        )

        leegality_doc.sign_url = sign_url

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

        leegality_doc.save()

        # =====================================
        # FINAL RESPONSE
        # STATUS COMES FROM WEBHOOK-UPDATED DB
        # =====================================

        return Response({

            "success": True,

            "document_id": leegality_doc.document_id,

            "status": leegality_doc.status,

            "sign_url": leegality_doc.sign_url,

            "completion_date": leegality_doc.completion_date,

            "used_signature_type":
                leegality_doc.used_signature_type,

            "signer_name":
                leegality_doc.signer_name,

            "signer_email":
                leegality_doc.signer_email,

            "signer_phone":
                leegality_doc.signer_phone,

            "invitation_status":
                leegality_doc.invitation_status,

            "webhook_payload":
                leegality_doc.webhook_payload,
        })

# class FetchLeegalityDocumentAPIView(APIView):

#     def get(self, request):

#         document_id = request.GET.get(
#             "document_id"
#         )

#         if not document_id:

#             return Response(
#                 {
#                     "error": "document_id required"
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         service = LeegalityService()

#         response = service.fetch_document_details(
#             document_id=document_id
#         )

#         print(response)

#         # =========================
#         # ACTUAL API DATA
#         # =========================

#         data = response.get(
#             "data",
#             {}
#         ).get(
#             "data",
#             {}
#         )

#         # =========================
#         # INVITEES
#         # =========================

#         invitees = data.get(
#             "invitees",
#             []
#         )

#         invitee_data = {}

#         if invitees:

#             invitee_data = invitees[0]

#         # =========================
#         # EXTRACT DATA
#         # =========================

#         sign_url = invitee_data.get(
#             "signUrl"
#         )

#         expiry_date = invitee_data.get(
#             "expiryDate"
#         )

#         signer_name = invitee_data.get(
#             "name"
#         )

#         signer_email = invitee_data.get(
#             "email"
#         )

#         signer_phone = invitee_data.get(
#             "phone"
#         )

#         active = invitee_data.get(
#             "active",
#             False
#         )

#         completion_date = data.get(
#             "completionDate"
#         )

#         used_signature_type = data.get(
#             "usedSignatureType"
#         )

        
#         # =========================
#         # STATUS
#         # =========================

#         status_from_api = data.get("status")

#         if status_from_api:
#             document_status = status_from_api.upper()

#         elif completion_date:
#             document_status = "SIGNED"

#         else:
#             document_status = "PENDING"

#         # =========================
#         # UPDATE DATABASE
#         # =========================

#         try:

#             leegality_doc = (
#                 LeegalityDocument.objects.get(
#                     document_id=document_id
#                 )
#             )

#             leegality_doc.sign_url = (
#                 sign_url
#             )

#             leegality_doc.used_signature_type = (
#                 used_signature_type
#             )

#             leegality_doc.completion_date = (
#                 completion_date
#             )

#             leegality_doc.invitation_status = (
#                 "ACTIVE"
#                 if active
#                 else "INACTIVE"
#             )

#             leegality_doc.status = (
#                 document_status
#             )

#             leegality_doc.save()

#         except LeegalityDocument.DoesNotExist:

#             return Response(
#                 {
#                     "error": "Document not found in DB"
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # =========================
#         # FINAL RESPONSE
#         # =========================

#         return Response({

#             "success": True,

#             "document_id": document_id,

#             "status": document_status,

#             "sign_url": sign_url,

#             "expiry_date": expiry_date,

#             "completion_date": completion_date,

#             "signer_name": signer_name,

#             "signer_email": signer_email,

#             "signer_phone": signer_phone,

#             "response": response
#         })
        
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator      
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json

@csrf_exempt
@api_view(["POST"])
def leegality_webhook(request):

    data = request.data

    print("WEBHOOK RECEIVED")
    print(json.dumps(data, indent=4))

    document_id = (
        data.get("documentId")
        or data.get("document_id")
    )

    status_value = (
        data.get("status")
        or data.get("documentStatus")
        or "PENDING"
    )

    completion_date = (
        data.get("completionDate")
        or data.get("completedAt")
    )

    if not document_id:

        return Response({
            "success": False,
            "message": "documentId missing"
        })

    try:

        doc = LeegalityDocument.objects.get(
            document_id=document_id
        )

        doc.status = status_value.upper()

        if completion_date:
            doc.completion_date = completion_date

        doc.webhook_payload = data
        doc.raw_response = data

        
        doc.save()

        print("DOCUMENT UPDATED")

    except LeegalityDocument.DoesNotExist:

        print("DOCUMENT NOT FOUND")

    return Response({
        "success": True
    })