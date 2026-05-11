# services/mobile360_service.py

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

from digitalverifications.models import Mobile360Log
from .mobile360 import SmartAuthClient


# =====================================================
# GET SELLING PRICE
# =====================================================
def get_mobile360_price(user):

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
            service="mobile360"
        ).order_by("-id").first()

        if custom:
            return custom.price

    # =====================================
    # AGENT DEFAULT PRICE
    # =====================================
    agent_price = AgentCibilPricing.objects.filter(
        agent=agent,
        customer__isnull=True,
        service="mobile360"
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
        return plan.plan.mobile360_price

    return 0


# =====================================================
# MAIN SERVICE
# =====================================================
class Mobile360Service:

    @staticmethod
    @transaction.atomic
    def check_mobile(user, mobile):

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
        cost_price = active_plan.plan.mobile360_price

        if not cost_price or cost_price <= 0:

            return {
                "success": False,
                "message": "Mobile360 price not configured"
            }

        # =====================================
        # CUSTOMER SELLING PRICE
        # =====================================
        selling_price = get_mobile360_price(user)

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
                service="mobile360",
                note="Mobile360 check"
            )

        # =====================================
        # API CALL
        # =====================================
        client = SmartAuthClient()

        response = client.call_api(mobile)

        # =====================================
        # FAILED => REFUND
        # =====================================
        if not response.get("status"):

            if customer:

                wallet_credit(
                    user=customer,
                    amount=selling_price,
                    service="mobile360",
                    note="Refund Mobile360 failed"
                )

            Mobile360Log.objects.create(
                agent=agent,
                customer=customer,
                mobile=mobile,
                txn_id=response.get("txn_id"),
                status="FAILED",
                cost_price=cost_price,
                selling_price=selling_price,
                profit=0,
                message=response.get("message"),
                response_data=response.get("data"),
                raw_response=response.get("raw"),
                reference_id=f"M360-{uuid.uuid4().hex[:10]}"
            )

            return {
                "success": False,
                "message": response.get("message")
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
        # SAVE LOG
        # =====================================
        profit = max(
            Decimal(selling_price) - Decimal(cost_price),
            0
        )

        Mobile360Log.objects.create(
            agent=agent,
            customer=customer,
            mobile=mobile,
            txn_id=response.get("txn_id"),
            status="SUCCESS",
            cost_price=cost_price,
            selling_price=selling_price,
            profit=profit,
            message=response.get("message"),
            response_data=response.get("data"),
            raw_response=response.get("raw"),
            reference_id=f"M360-{uuid.uuid4().hex[:10]}"
        )

        return {
            "success": True,
            "message": "Mobile360 success",
            "data": response.get("data"),
            "txn_id": response.get("txn_id")
        }