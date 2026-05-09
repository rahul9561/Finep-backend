# services/leegality_pricing_service.py

from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
import uuid

from wallet.models import Wallet
from wallet.services import wallet_debit, wallet_credit

from cibil.models import (
    AgentPlan,
    AgentCibilPricing
)

from esign.models import LeegalityDocument

from services.leegality_service import LeegalityService


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

    # =====================================
    # CUSTOMER CUSTOM PRICE
    # =====================================
    if customer:

        custom = AgentCibilPricing.objects.filter(
            agent=agent,
            customer=customer,
            service="leegality_esign"
        ).order_by("-id").first()

        if custom:
            return custom.price

    # =====================================
    # AGENT DEFAULT PRICE
    # =====================================
    agent_price = AgentCibilPricing.objects.filter(
        agent=agent,
        customer__isnull=True,
        service="leegality_esign"
    ).order_by("-id").first()

    if agent_price:
        return agent_price.price

    # =====================================
    # FALLBACK PLAN PRICE
    # =====================================
    plan = AgentPlan.objects.filter(
        agent=agent,
        is_active=True
    ).last()

    if plan:
        return plan.plan.leegality_esign_price

    return 0


# =====================================================
# MAIN SERVICE
# =====================================================
class LeegalityPricingService:

    @staticmethod
    @transaction.atomic
    def create_esign(
        user,
        file_name,
        base64_file,
        signer_name,
        signer_email,
        signer_phone,
        irn
    ):

        # =====================================
        # USER IDENTIFY
        # =====================================
        if hasattr(user, "created_by") and user.created_by:
            customer = user
            agent = user.created_by
        else:
            customer = None
            agent = user

        # =====================================
        # PLAN CHECK
        # =====================================
        agent_plan = AgentPlan.objects.select_for_update().filter(
            agent=agent,
            is_active=True
        ).order_by("created_at")

        if not agent_plan.exists():

            return {
                "success": False,
                "message": "Please recharge plan"
            }

        active_plan = agent_plan.last()

        # =====================================
        # AGENT COST PRICE
        # =====================================
        cost_price = active_plan.plan.leegality_esign_price

        if not cost_price or cost_price <= 0:

            return {
                "success": False,
                "message": "Leegality price not configured"
            }

        # =====================================
        # CUSTOMER SELLING PRICE
        # =====================================
        selling_price = get_leegality_price(user)

        # =====================================
        # BALANCE CHECK
        # =====================================
        total_balance = agent_plan.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        if total_balance < cost_price:

            return {
                "success": False,
                "message": "Insufficient balance"
            }

        # =====================================
        # CUSTOMER WALLET CHECK
        # =====================================
        if customer:

            wallet = Wallet.objects.filter(
                user=customer
            ).first()

            if not wallet or wallet.balance < selling_price:

                return {
                    "success": False,
                    "message": "Insufficient wallet balance"
                }

            # CUSTOMER DEBIT
            wallet_debit(
                user=customer,
                amount=selling_price,
                service="leegality_esign",
                note="Leegality Aadhaar eSign"
            )

        # =====================================
        # API CALL
        # =====================================
        service = LeegalityService()

        response = service.create_sign_request(
            file_name=file_name,
            base64_file=base64_file,
            signer_name=signer_name,
            signer_email=signer_email,
            signer_phone=signer_phone,
            irn=irn
        )

        data = response.get("data", {})

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

            return {
                "success": False,
                "message": data.get("message", "API failed"),
                "data": data
            }

        # =====================================
        # AGENT PLAN DEDUCTION
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
        # PROFIT
        # =====================================
        profit = max(
            Decimal(selling_price) - Decimal(cost_price),
            0
        )

        # =====================================
        # SAVE DOCUMENT
        # =====================================
        LeegalityDocument.objects.create(
            user=user,
            file_name=file_name,
            signer_name=signer_name,
            signer_email=signer_email,
            signer_phone=signer_phone,
            irn=irn,
            document_id=data.get("documentId"),
            status="SUCCESS",
            cost_price=cost_price,
            selling_price=selling_price,
            profit=profit,
            reference_id=f"ESIGN-{uuid.uuid4().hex[:10]}",
            raw_response=data
        )

        return {
            "success": True,
            "message": "eSign request created successfully",
            "data": data
        }