from django.utils import timezone
from datetime import timedelta, datetime
from django.db import transaction
from django.db.models import Sum
from django.core.files.base import ContentFile
from django.core.files.base import ContentFile
import requests
import base64
from cibil.models import CibilReport, AgentPlan, PlanUsage, AgentCibilPricing
from wallet.services import wallet_debit, wallet_credit
from .BeFiSc import SmartAuthClient

import re
import uuid
import logging

logger = logging.getLogger(__name__)


class BeFicCibilService:

    @staticmethod
    def get_dynamic_price(user, service):

        if hasattr(user, "created_by") and user.created_by:
            agent = user.created_by
            customer = user
        else:
            agent = user
            customer = None

        # customer custom pricing
        if customer:
            custom = AgentCibilPricing.objects.filter(
                agent=agent,
                customer=customer,
                service=service
            ).order_by("-id").first()

            if custom:
                return custom.price

        # agent default pricing
        agent_price = AgentCibilPricing.objects.filter(
            agent=agent,
            customer__isnull=True,
            service=service
        ).order_by("-id").first()

        if agent_price:
            return agent_price.price

        # fallback plan
        plan = AgentPlan.objects.filter(
            agent=agent,
            is_active=True
        ).last()

        if plan:
            return getattr(plan.plan, f"{service}_price", 0)

        return 0

    @staticmethod
    @transaction.atomic
    def generate_report(user, data):

        # =========================
        # USER IDENTIFY
        # =========================
        if hasattr(user, "created_by") and user.created_by:
            customer = user
            agent = user.created_by
        else:
            customer = None
            agent = user

        pan = (data.get("pan") or "").upper().strip()
        mobile = str(data.get("mobile") or "").strip()
        name = data.get("name")
        report_type = data.get("report_type")

        # =========================
        # VALIDATION
        # =========================
        if not pan:
            return {"success": False, "message": "PAN required"}

        if not re.match(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan):
            return {"success": False, "message": "Invalid PAN"}

        if not re.match(r"^[6-9]\d{9}$", mobile):
            return {"success": False, "message": "Invalid mobile"}

        ALLOWED = ["cibil_advanced", "only_score"]
        if report_type not in ALLOWED:
            return {"success": False, "message": "Invalid report type"}

        # =========================
        # PLAN CHECK
        # =========================
        agent_plans = AgentPlan.objects.select_for_update().filter(
            agent=agent,
            is_active=True
        ).order_by("created_at")

        if not agent_plans.exists():
            return {"success": False, "message": "Recharge required"}

        active_plan = agent_plans.last()
        plan = active_plan.plan
        
        
        PRICE_MAP = {
            "cibil_advanced": "cibil_advanced_price",
            "only_score": "only_score_price",
        }

        field = PRICE_MAP.get(report_type)

        if not field:
            return {"success": False, "message": "Invalid pricing config"}

        cost_price = getattr(plan, field, 0)

        # cost_price = getattr(plan, f"{report_type}_price", 0)
        selling_price = BeFicCibilService.get_dynamic_price(user, report_type)

        if cost_price <= 0:
            return {"success": False, "message": "Plan price not set"}

        if selling_price <= 0:
            return {"success": False, "message": "Selling price not set"}

        total_balance = agent_plans.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        if total_balance < cost_price:
            return {"success": False, "message": "Insufficient balance"}

        # =========================
        # CUSTOMER WALLET CHECK
        # =========================
        if customer:
            from wallet.models import Wallet

            wallet = Wallet.objects.filter(user=customer).first()

            if not wallet or wallet.balance < selling_price:
                return {
                    "success": False,
                    "message": "Insufficient wallet balance"
                }

            wallet_debit(
                user=customer,
                amount=selling_price,
                service=report_type,
                note=f"{report_type} report"
            )

        # =========================
        # CREATE REPORT
        # =========================
        report = CibilReport.objects.create(
            agent=agent,
            name=name or "Unknown",
            mobile=mobile,
            pan=pan,
            report_type=report_type,
            status="PENDING"
        )

        # =========================
        # API CALL
        # =========================
        client = SmartAuthClient()

        api_response = client.call_api(
            service_type=report_type,
            name=name,
            mobile=mobile,
            pan=pan
        )
        print("========== API RESPONSE ==========")
        print(api_response)
        print("==================================")

        # =========================
        # FAILURE HANDLE + REFUND
        # =========================
        if not api_response.get("status"):

            if customer:
                wallet_credit(
                    user=customer,
                    amount=selling_price,
                    service=report_type,
                    note="Refund (API failed)"
                )

            report.status = "FAILED"
            report.response_message = api_response.get("message")
            report.save()

            return {
                "success": False,
                "message": api_response.get("message")
            }

        # =========================
        # SUCCESS SAVE
        # =========================
        report.status = "SUCCESS"
        report.response_message = "Success"
        # PDF URL case
        pdf_url = api_response.get("pdf_url")

        if pdf_url:
            response = requests.get(pdf_url)

            if response.status_code == 200:
                report.report_pdf.save(
                    f"{pan}.pdf",
                    ContentFile(response.content),
                    save=False
                )

        # BASE64 PDF case
        pdf_base64 = api_response.get("pdf_base64")

        if pdf_base64:
            pdf_content = base64.b64decode(pdf_base64)

            report.report_pdf.save(
                f"{pan}.pdf",
                ContentFile(pdf_content),
                save=False
            )
        report.save()

        # =========================
        # PLAN DEDUCT (FIFO)
        # =========================
        remaining_price = cost_price

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

        # =========================
        # USAGE LOG
        # =========================
        profit = max(selling_price - cost_price, 0)

        PlanUsage.objects.create(
            agent=agent,
            customer=customer,
            report=report,
            service=report_type,
            cost_price=cost_price,
            price=selling_price,
            profit=profit,
            status="SUCCESS",
            reference_id=f"{report_type.upper()}-{uuid.uuid4().hex[:8]}"
        )

        return {
            "success": True,
            "data": api_response.get("data"),
            "txn_id": api_response.get("txn_id")
        }