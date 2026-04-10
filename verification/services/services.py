from django.db import transaction
from wallet.services import wallet_debit
from cibil.models import AgentPlan
from django.db.models import Sum
from cibil.services.service import get_dynamic_price
from django.db import transaction
from decimal import Decimal
from cibil.models import PlanUsage ,AgentCibilPricing
import uuid
from .clients import SurepassClient
from verification.models import (
    BankVerificationReport,
    PanVerificationReport,
    AadhaarValidationReport,
    GSTReport,
    MSMEReport,
    RCReport,
    ElectricityReport,
    
)


# -----------------------------
# COMMON WALLET HANDLER
# -----------------------------

def _deduct_and_save(user, service, report_model, report_kwargs, client_fn, *client_args):

    # price = Decimal(get_price(user, service))

    client = SurepassClient()
    SERVICE_PRICE_MAP = {
    "pan": "pan_verify_price",
    "gst": "gst_verify_price",
    "bank": "bank_verify_price",
    "aadhaar": "aadhaar_price",
    }

    SERVICE_DB_MAP = {
        "aadhaar": "aadhaar_verify",
        "pan": "pan_verify",
        "gst": "gst_verify",
        "bank": "bank_verify",
    }

    with transaction.atomic():

        # ✅ 1. PRE CHECK WALLET
        # if user.wallet.balance < price:
        #     return False, {"message": "Insufficient balance"}
        agent = user.created_by if user.role == "customer" else user

        agent_plans = AgentPlan.objects.select_for_update().filter(
            agent=agent,
            is_active=True
        )

        if not agent_plans.exists():
            return False, {"message": "Please recharge plan"}

        plan = agent_plans.last().plan

        # 🔥 dynamic pricing
        # selling_price = get_dynamic_price(user, service)
        # if user.role == "customer":
        #     pricing = AgentCibilPricing.objects.filter(
        #         agent=agent,
        #         service=service
        #     ).first()

        #     selling_price = pricing.price if pricing else plan_price
        # else:
        #     selling_price = get_dynamic_price(user, service)
        # 🔥 cost price from plan (PEHLE DEFINE KARO)
        # plan_price = getattr(plan, f"{service}_price", 0)
        field_name = SERVICE_PRICE_MAP.get(service, f"{service}_price")
        plan_price = getattr(plan, field_name, 0)

        # 🔥 selling price
        # if user.role == "customer":
            # pricing = AgentCibilPricing.objects.filter(
            #     agent=agent,
            #     service=service
            # ).first()
        #     pricing = AgentCibilPricing.objects.filter(
        #         agent=agent,
        #         service=db_service
        #     ).first()

        #     selling_price = pricing.price if pricing else plan_price
        # else:
        #     selling_price = get_dynamic_price(user, service)
        if user.role == "customer":
            db_service = SERVICE_DB_MAP.get(service, service)

    # 🔥 1. FIRST: customer specific pricing
            pricing = AgentCibilPricing.objects.filter(
                agent=agent,
                # customer_id=user.id,
                customer=user,
                service=db_service
            ).order_by("-created_at").first()

            # 🔥 2. FALLBACK: agent default pricing
            if not pricing:
                pricing = AgentCibilPricing.objects.filter(
                    agent=agent,
                    customer__isnull=True,
                    service=db_service
                ).first()

            selling_price = pricing.price if pricing else plan_price

        else:
            selling_price = get_dynamic_price(user, service)

        # 🔥 cost price from plan

        total_balance = agent_plans.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        if total_balance < plan_price:
            return False, {"message": "Insufficient balance"}
        

        # ✅ 2. TEMP DEDUCT (SAFE)
        # wallet_debit(
        #     user=user,
        #     amount=price,
        #     service=service,
        #     note="Verification charge (hold)"
        # )
        # 🔥 CUSTOMER WALLET DEDUCT
        if user.role == "customer":
            from wallet.services import wallet_debit

            wallet_debit(
                user=user,
                amount=selling_price,
                service=service,
                note="Customer API usage"
            )

        # ✅ 3. CALL API
        data = client_fn(*client_args)

        provider_status = data.get("status_code", 500)
        api_ok = provider_status in [200, 422]

        # ❌ FAIL CASE → REFUND
        if not api_ok:

            # refund
            # 🔥 refund customer if API fails
            if user.role == "customer":
                from wallet.services import wallet_credit

                wallet_credit(
                    user=user,
                    amount=selling_price,
                    service=service,
                    note="Refund (API failed)"
                )

            report_model.objects.create(
                user=user,
                response=data,
                status=False,
                **report_kwargs
            )

            return False, {
                "message": data.get("message", "Verification failed"),
                "provider_response": data,
            }

        # ✅ SUCCESS CASE
        report = report_model.objects.create(
            user=user,
            response=data,
            status=True,
            **report_kwargs
        )
        remaining_price = plan_price

        for p in agent_plans:
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
                
        profit = max(selling_price - plan_price, 0)

        PlanUsage.objects.create(
            agent=agent,
            customer=user if user.role == "customer" else None,
            service=service,
            cost_price=plan_price,
            price=selling_price,
            profit=profit,
            status="SUCCESS",
            report=report if service == "cibil" else None,  # ✅ safe
            reference_id=f"{service.upper()}-{uuid.uuid4().hex[:10]}"
        )
        

    return True, data


# =====================
# SERVICES
# =====================

def bank_verification_service(user, id_number, ifsc):
    ok, data = _deduct_and_save(
        user, "bank",
        BankVerificationReport,
        {"id_number": id_number, "ifsc": ifsc},
        SurepassClient().bank_verification, id_number, ifsc,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}


def pan_verification_service(user, id_number, full_name, dob):
    ok, data = _deduct_and_save(
        user, "pan",
        PanVerificationReport,
        {"pan_number": id_number, "full_name": full_name, "dob": dob},
        SurepassClient().pan_verify, id_number, full_name, dob,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}


def aadhaar_validation_service(user, id_number):
    ok, data = _deduct_and_save(
        user, "aadhaar",
        AadhaarValidationReport,
        {"aadhaar_number": id_number},
        SurepassClient().aadhaar_validation, id_number,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}


def gst_service(user, id_number):
    ok, data = _deduct_and_save(
        user, "gst",
        GSTReport,
        {"gst_number": id_number},
        SurepassClient().gst_verify, id_number,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}


def msme_service(user, pan):
    ok, data = _deduct_and_save(
        user, "msme",
        MSMEReport,
        {"pan": pan},
        SurepassClient().pan_to_msme, pan,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}


def rc_service(user, rc_number):
    ok, data = _deduct_and_save(
        user, "rc",
        RCReport,
        {"rc_number": rc_number},
        SurepassClient().rc_verify, rc_number,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}


def electricity_service(user, id_number, operator_code):
    ok, data = _deduct_and_save(
        user, "electricity",
        ElectricityReport,
        {"id_number": id_number, "operator_code": operator_code},
        SurepassClient().electricity_verify, id_number, operator_code,
    )
    return {"status": ok, "data": data} if ok else {"status": False, **data}