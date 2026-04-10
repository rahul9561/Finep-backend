#service/service.py
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from cibil.models import CibilReport, AgentPlan, PlanUsage
from .client import BureauClient
from django.db import transaction
from django.db.models import Sum
from datetime import timedelta, datetime
from cibil.models import AgentCibilPricing, AgentPlan
import re
from wallet.services import wallet_debit
import uuid
from difflib import SequenceMatcher
import logging
logger = logging.getLogger(__name__)



def normalize_name(name):
    return " ".join(name.split()).title()

def extract_name(data, fallback=None):
    return (
        data.get("full_name")
        or data.get("name")
        or fallback
        or ""
    ).strip()


def get_dynamic_price(user, service):

    if hasattr(user, "created_by") and user.created_by:
        agent = user.created_by
        customer = user
    else:
        agent = user
        customer = None

    # customer specific
    if customer:
        custom = AgentCibilPricing.objects.filter(
            agent=agent,
            customer=customer,
            service=service
        ).order_by("-id").first()

        if custom:
            return custom.price

    # agent default
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




def extract_state_pincode(address):

    state = None
    pincode = None

    if not address:
        return None, None

    # find pincode
    m = re.search(r"\b\d{6}\b", address)
    if m:
        pincode = m.group()

    # find state code (last 2 capital letters)
    m = re.search(r"\b([A-Z]{2})\b\s*$", address.strip())
    if m:
        state = m.group(1)

    return state, pincode



class CibilService:

    @staticmethod
    def check_duplicate(pan, report_type):
        return CibilReport.objects.filter(
            pan=pan,
            report_type=report_type,
            status="SUCCESS",
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).first()

    @staticmethod
    @transaction.atomic
    def generate_report(agent, data):
        # 🔥 identify user type
        user = agent   # jo pass ho raha hai

        customer = None

        # if hasattr(user, "created_by") and user.created_by:
        #     customer = user
        #     agent = user.created_by
        if hasattr(user, "created_by") and user.created_by:
            customer = user
            agent = user.created_by
        else:
            agent = user

        pan = (data.get("pan") or "").upper().strip()
        if not pan:
            return {
                "success": False,
                "message": "PAN required"
            }
        report_type = data.get("report_type")

        mobile = str(data.get("mobile") or "").strip()
        name = data.get("name")

        # ✅ PAN validation
        if not pan or not re.match(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan):
            return {"success": False, "message": "Invalid PAN format"}

        # ✅ report type validation
        ALLOWED = ["cibil", "crif", "experian", "equifax", "multi"]

        if report_type not in ALLOWED:
            return {"success": False, "message": "Invalid report type"}

        # =========================
        # 1️⃣ DUPLICATE CHECK
        # =========================

        # existing = CibilService.check_duplicate(pan, report_type)
        existing = None

        # if existing and existing.report_pdf:
        # if existing and existing.report_pdf and existing.status == "SUCCESS":
        # if existing:
        #     pass

        #     existing.report_pdf.open("rb")
        #     file_data = existing.report_pdf.read()
        #     existing.report_pdf.close()
            
        #     price = getattr(plan, f"{report_type}_price", 0)

        #     PlanUsage.objects.create(
        #         agent=agent,
        #         report=existing,
        #         service=report_type,
        #         price=price
        #     )

        #     return {
        #         "success": True,
        #         "file": file_data,
        #         "cached": True
        #     }

        # =========================
        # 2️⃣ PREFILL CHECK HERE ✅
        # =========================

        try:

            prefill = BureauClient.fetch_prefill(
                mobile=mobile,
                first_name=name
            )

            if prefill.get("success"):

                pdata = prefill.get("data", {})

                prefill_pan = (pdata.get("pan") or "").upper()

                if prefill_pan and pan and prefill_pan != pan:

                    return {
                        "success": False,
                        "message": "PAN mismatch with mobile"
                    }

        except Exception as e:

            logger.error(f"Prefill error: {e}")
            
            return {
                "success": False,
                "message": "Prefill failed"
            }

        # =========================
        # 3️⃣ PLAN CHECK
        # =========================

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
        plan = active_plan.plan

        # ✅ prices
        plan_price = getattr(plan, f"{report_type}_price", None)
        # selling_price = get_dynamic_price(customer or agent, report_type)
        selling_price = get_dynamic_price(user, report_type)

        # ✅ validation
        if plan_price is None or plan_price <= 0:
            return {"success": False, "message": "Plan price not configured"}

        if selling_price is None or selling_price <= 0:
            return {"success": False, "message": "Invalid report type"}
        
        total_balance = agent_plan.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0
        
        if total_balance < plan_price:
            return {
                "success": False,
                "message": "Insufficient balance"
            }

        debit_user = customer if customer else user

        wallet_debit(
            user=debit_user,
            amount=selling_price,
            service=report_type,
            note=f"{report_type} report generated"
        )

        

        # =========================
        # 4️⃣ CREATE REPORT RECORD
        # =========================
        if not pan:
            return {
                "success": False,
                "message": "Invalid PAN"
            }
            
        prefill_data = prefill.get("data", {}) if prefill else {}
        name_value = normalize_name(extract_name(prefill_data, name))
        
        

        report = CibilReport.objects.create(
            agent=agent,
            name=name_value,
            mobile=mobile,
            pan=pan,
            report_type=report_type,
            status="PENDING",
            # request_data=payload 
        )

        # =========================
        # 5️⃣ PAYLOAD
        # =========================

        gender = (data.get("gender") or "").lower()


        dob = data.get("dob")
        # convert dob to YYYY-MM-DD
        if dob:
            try:
                dob = datetime.strptime(dob, "%d-%m-%Y").strftime("%Y-%m-%d")
            except:
                dob = None
                
        
        
        addresses = prefill_data.get("addresses") or []

        address = addresses[0] if addresses else None

        state, pincode = extract_state_pincode(address)

        

        payload = {
            "name": name_value,
            "mobile": mobile,
            "pan_card": pan,
            "report_type": report_type,
            "gender": gender,
            "consent": "Y",
        }

        if report_type == "equifax":
            
            payload.update({
                "dob": dob,
                "address": address,
                "state": state,
                "pincode": pincode,
            })

        if report_type == "multi":

            payload["bureau"] = "ALL"

        payload = {k: v for k, v in payload.items() if v}

        logger.info(f"VERIFYAL PAYLOAD: {payload}")

        # =========================
        # 6️⃣ API CALL
        # =========================

        result = BureauClient.generate_report(
            report_type,
            payload
        )

        if not result.get("success"):
            if customer:
                from wallet.services import wallet_credit
                try:
                    wallet_credit(
                        user=debit_user, 
                        amount=selling_price,
                        service=report_type,
                        note="Refund (API failed)"
                    )
                except Exception as e:
                    return {
                        "success": False,
                        "message": str(e)
                    }

            report.status = "FAILED"
            report.response_message = result.get("message")
            report.save()

            return {
                "success": False,
                "message": result.get("message")
            }

        # =========================
        # 7️⃣ SAVE PDF
        # =========================

        pdf_file = result.get("file")

        report.report_pdf.save(
            f"{pan}_{report_type}.pdf",
            ContentFile(pdf_file)
        )

        report.status = "SUCCESS"
        report.save()

        # =========================
        # 8️⃣ FIFO BALANCE
        # =========================

        # remaining_price = price
        remaining_price = plan_price

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
        # 9️⃣ USAGE
        # =========================
        
        # profit = selling_price - plan_price
        profit = max(selling_price - plan_price, 0)

        if profit < 0:
            profit = 0

        PlanUsage.objects.create(
            agent=agent,
            report=report,
            service=report_type,
            cost_price=plan_price,   # 🔥 ADD THIS
            price=selling_price,
            status="SUCCESS",
            profit=profit,
            reference_id = f"{report_type.upper()}-{uuid.uuid4().hex[:10]}"
        )

        return {
            "success": True,
            "file": pdf_file
        }