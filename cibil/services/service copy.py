#service/service.py
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from cibil.models import CibilReport, AgentPlan, PlanUsage
from .client import BureauClient
from django.db import transaction
from django.db.models import Sum
import re
from difflib import SequenceMatcher

import logging
logger = logging.getLogger(__name__)




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

        # mobile = data.get("mobile")
        pan = data.get("pan").upper()
        # name = data.get("name")
        report_type = data.get("report_type")

        # 🔒 PAN format check
        if not pan or not re.match(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan):
                return {"success": False, "message": "Invalid PAN format"}

        # 1️⃣ Duplicate check
        existing = CibilService.check_duplicate(pan, report_type)

        if existing and existing.report_pdf:
            existing.report_pdf.open("rb")
            file_data = existing.report_pdf.read()
            existing.report_pdf.close()

            # usage tracking
            PlanUsage.objects.create(
                agent=agent,
                report=existing,
                service=report_type,
                price=0   # cached report free hai to 0
            )

            return {
                "success": True,
                "file": file_data,
                "cached": True
            }


        # 🔎 Prefill validation
        # try:
        #     prefill = BureauClient.fetch_prefill(mobile)
        #     if prefill.get("success"):
        #         prefill_data = prefill.get("data", {})
        #         prefill_pan = (prefill_data.get("pan") or "").upper()
        #         prefill_name = (prefill_data.get("name") or "").lower()

        #         # if prefill_pan and prefill_pan != pan.upper():
        #         #     return {
        #         #         "success": False,
        #         #         "message": "PAN does not match mobile"
        #         #     }

        #         # similarity = SequenceMatcher(
        #         #     None,
        #         #     name.lower(),
        #         #     prefill_name
        #         # ).ratio()
        #         # if similarity < 0.6:
        #         #     return {
        #         #         "success": False,
        #         #         "message": "Name mismatch with PAN records"
        #         #     }
        #         if name and prefill_name:
        #             similarity = SequenceMatcher(
        #                 None,
        #                 name.lower(),
        #                 prefill_name
        #             ).ratio()

        #             if similarity < 0.6:
        #                 return {
        #                     "success": False,
        #                     "message": "Name mismatch with PAN records"
        #                 }

        # except Exception:
        #         pass


        # 🔒 Check agent active plan
        # agent_plan = AgentPlan.objects.filter(
        agent_plan = AgentPlan.objects.select_for_update().filter(
            agent=agent,
            is_active=True
        ).order_by("created_at")

        if not agent_plan.exists():
            return {
                "success": False,
                "message": "Please purchase a recharge plan first"
            }

        # 💰 Get price based on report type
        plan = agent_plan.last().plan

        # price_map = {
        #     "cibil": plan.cibil_price,
        #     "crif": plan.crif_price,
        #     "equifax": plan.equifax_price,
        #     "experian": plan.experian_price
        # }

        # price = price_map.get(report_type)
        price = getattr(plan, f"{report_type}_price", None)
        

        if not price:
            return {
                "success": False,
                "message": "Invalid report type"
            }

        # if agent_plan.remaining_balance < price:
        # total_balance = sum(p.remaining_balance for p in agent_plan)
        total_balance = agent_plan.aggregate(
                total=Sum("remaining_balance")
        )["total"] or 0
        if total_balance < price:
            return {
                "success": False,
                "message": "Insufficient plan balance"
            }

        
            # 2️⃣ Create DB record
        report = CibilReport.objects.create(
                agent=agent,
                full_name=data.get("name"),
                mobile=data.get("mobile"),
                pan=pan,
                report_type=report_type,
                dob=data.get("dob") or None,
                address=data.get("address") or None,
                state=data.get("state") or None,
                pincode=data.get("pincode") or None,
                status="PENDING"
            )
       

        # 3️⃣ Prepare payload
        gender = (data.get("gender") or "").lower()
        mobile = str(data.get("mobile") or "").strip()

        payload = {
            "name": data.get("name"),
            "mobile": mobile,
            "pan_card": pan,
            "report_type": report_type,
            "consent": "Y"
        }

        # only for equifax
        if report_type == "equifax":
            payload.update({
                "gender": gender,
                "dob": data.get("dob").strftime("%Y-%m-%d") if data.get("dob") else None,
                "address": data.get("address"),
                "state": data.get("state"),
                "pincode": data.get("pincode"),
            })
        else:
            payload["gender"] = gender

        payload = {k: v for k, v in payload.items() if v}

        # print("VERIFYAL PAYLOAD:", payload)
        # print("VERIFYAL PAYLOAD:", report_type, payload)
        logger.info(f"VERIFYAL PAYLOAD {report_type}: {payload}")

        # 4️⃣ Call API
        result = BureauClient.generate_report(report_type, payload)
        logger.info(f"Bureau result: {result}")

        if not result.get("success"):

            report.status = "FAILED"
            report.response_message = result.get("message")
            report.save()

            return {
                "success": False,
                "message": result.get("message")
            }

        # 5️⃣ Save PDF
        pdf_file = result.get("file")

        report.report_pdf.save(
            f"{pan}_{report_type}.pdf",
            ContentFile(pdf_file)
        )

        report.status = "SUCCESS"
        report.save()

        # 💸 Deduct plan balance
        # agent_plan.remaining_balance -= price
        # agent_plan.save()
        # 🔥 FIFO balance deduction

        # agent_plan = AgentPlan.objects.filter(
        #     agent=agent,
        #     is_active=True
        # ).order_by("created_at")
        plans = agent_plan

        remaining_price = price
        
        for plan in plans:
        # for plan in agent_plan:

            # if this plan has enough balance
            if plan.remaining_balance >= remaining_price:

                plan.remaining_balance -= remaining_price

                if plan.remaining_balance == 0:
                    plan.is_active = False

                plan.save()
                break

            # if balance not enough
            else:

                remaining_price -= plan.remaining_balance
                plan.remaining_balance = 0
                plan.is_active = False
                plan.save()

        # 📊 Save usage
        PlanUsage.objects.create(
            agent=agent,
            report=report,
            service=report_type,
            price=price
        )

        # 🔴 Auto deactivate if balance finished
        # if agent_plan.remaining_balance <= 0:
        #     agent_plan.is_active = False
        #     agent_plan.save()

        

        return {
            "success": True,
            "file": pdf_file
        }