from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from cibil.models import CibilReport, AgentPlan, PlanUsage, AgentCibilPricing
from .prefill import SurepassClient
from django.db import transaction
from django.db.models import Sum
import re
import uuid
import logging

logger = logging.getLogger(__name__)


def get_dynamic_price(user, report_type):
    """
    Returns selling price (customer price)
    """

    if hasattr(user, "created_by") and user.created_by:
        agent = user.created_by
        customer = user
    else:
        agent = user
        customer = None

    # Customer-specific pricing
    if customer:
        custom = AgentCibilPricing.objects.filter(
            agent=agent,
            customer=customer,
            service=report_type
        ).order_by("-id").first()

        if custom:
            return custom.price

    # Agent default pricing
    agent_price = AgentCibilPricing.objects.filter(
        agent=agent,
        customer__isnull=True,
        service=report_type
    ).order_by("-id").first()

    if agent_price:
        return agent_price.price

    # fallback to plan price
    plan = AgentPlan.objects.filter(agent=agent, is_active=True).last()
    if plan:
        return getattr(plan.plan, f"{report_type}_price", 0)

    return 0


class SureCibilService:

    @staticmethod
    @transaction.atomic
    def generate_report(user, data):

        import requests

        # =========================
        # IDENTIFY AGENT / CUSTOMER
        # =========================
        if hasattr(user, "created_by") and user.created_by:
            customer = user
            agent = user.created_by
        else:
            customer = None
            agent = user

        pan = (data.get("pan") or "").upper().strip()
        report_type = data.get("report_type")
        mobile = str(data.get("mobile") or "").strip()
        name = data.get("name")

        # =========================
        # VALIDATION
        # =========================
        if not pan:
            return {"success": False, "message": "PAN required"}

        if not re.match(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan):
            return {"success": False, "message": "Invalid PAN format"}

        if not re.match(r"^[6-9]\d{9}$", mobile):
            return {"success": False, "message": "Invalid mobile number"}

        if report_type not in ["crif", "equifax", "experian"]:
            return {"success": False, "message": "Invalid report type"}

        # =========================
        # PLAN CHECK (AGENT)
        # =========================
        agent_plan = AgentPlan.objects.select_for_update().filter(
            agent=agent,
            is_active=True
        ).order_by("created_at")

        if not agent_plan.exists():
            return {"success": False, "message": "Please recharge plan"}

        active_plan = agent_plan.last()
        plan = active_plan.plan

        cost_price = getattr(plan, f"{report_type}_price", None)

        total_balance = agent_plan.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        if total_balance < cost_price:
            return {"success": False, "message": "Insufficient balance"}

        # =========================
        # SELLING PRICE
        # =========================
        selling_price = get_dynamic_price(user, report_type)

        if not selling_price:
            return {"success": False, "message": "Pricing not configured"}

        # =========================
        # CREATE REPORT
        # =========================
        report = CibilReport.objects.create(
            agent=agent,
            name=name,
            mobile=mobile,
            pan=pan,
            report_type=report_type,
            status="PENDING",
        )

        # =========================
        # API CALL
        # =========================
        client = SurepassClient()

        if report_type == "crif":
            parts = (name or "").split()
            result = client.crif_report_pdf(
                first_name=parts[0],
                last_name=" ".join(parts[1:]) or "NA",
                mobile=mobile,
                pan=pan
            )

        elif report_type == "equifax":
            result = client.equifax_report_pdf_v2(
                name=name,
                pan=pan,
                mobile=mobile,
                gender=(data.get("gender") or "male")
            )

        else:  # experian
            result = client.experian_report_pdf(
                name=name,
                mobile=mobile,
                pan=pan
            )

        # =========================
        # FAILURE → NO WALLET CUT
        # =========================
        if not result.get("success"):
            report.status = "FAILED"
            report.response_message = result.get("message")
            report.save()

            return {
                "success": False,
                "message": result.get("message")
            }

        # =========================
        # HANDLE PDF (FINAL FIX)
        # =========================
        pdf_file = result.get("file")
        pdf_url = result.get("pdf_url")

        try:

            # 🔥 CRIF / Equifax
            if pdf_file:
                report.report_pdf.save(
                    f"{pan}_{report_type}.pdf",
                    ContentFile(pdf_file)
                )

            # 🔥 Experian (download from URL)
            elif pdf_url:
                pdf_res = requests.get(pdf_url, timeout=30)

                if pdf_res.status_code != 200:
                    raise Exception("Failed to download PDF")

                report.report_pdf.save(
                    f"{pan}_{report_type}.pdf",
                    ContentFile(pdf_res.content)
                )

            else:
                raise Exception("PDF not found")

        except Exception as e:
            report.status = "FAILED"
            report.response_message = str(e)
            report.save()

            return {
                "success": False,
                "message": "PDF processing failed"
            }

        # =========================
        # SUCCESS SAVE
        # =========================
        report.status = "SUCCESS"
        report.save()

        # =========================
        # WALLET DEDUCT (AFTER SUCCESS)
        # =========================
        if customer:
            from wallet.services import wallet_debit

            wallet_debit(
                user=customer,
                amount=selling_price,
                service=report_type,
                note=f"{report_type} report generated"
            )

        # =========================
        # AGENT PLAN DEDUCTION
        # =========================
        remaining_price = cost_price

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

        # =========================
        # USAGE TRACK
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
            reference_id=f"{report_type.upper()}-{uuid.uuid4().hex[:10]}"
        )

        return {
            "success": True
        }