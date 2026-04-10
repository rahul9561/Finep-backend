from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum
from cibil.models import AgentPlan, PlanUsage, CibilReport
from .services.client import BureauClient
from .permissions import IsAdminUserCustom


class AdminPrefillView(APIView):

    permission_classes = [IsAdminUserCustom]

    @transaction.atomic
    def post(self, request):

        admin = request.user

        mobile = request.data.get("mobile")
        name = request.data.get("name")

        if not mobile or not name:
            return Response({
                "success": False,
                "message": "Mobile and name required"
            })

        # -----------------
        # PLAN CHECK
        # -----------------

        plans = AgentPlan.objects.select_for_update().filter(
            agent=admin,
            is_active=True
        ).order_by("created_at")

        if not plans.exists():

            return Response({
                "success": False,
                "message": "Admin plan not found"
            })

        price = plans.last().plan.prefill_price

        total = plans.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        if total < price:

            return Response({
                "success": False,
                "message": "Insufficient balance"
            })

        # -----------------
        # API
        # -----------------

        result = BureauClient.fetch_prefill(
            mobile,
            name
        )

        if result.get("status") != 200:

            return Response({
                "success": False,
                "message": result.get("message")
            })

        data = result.get("data", {})

        report = CibilReport.objects.create(
            agent=admin,
            full_name=data.get("full_name") or name,
            mobile=mobile,
            pan=(data.get("pan_number") or [None])[0],
            report_type="prefill",
            status="SUCCESS"
        )

        # -----------------
        # BALANCE CUT
        # -----------------

        remaining = price

        for p in plans:

            if p.remaining_balance >= remaining:

                p.remaining_balance -= remaining

                if p.remaining_balance == 0:
                    p.is_active = False

                p.save()
                break

            else:

                remaining -= p.remaining_balance
                p.remaining_balance = 0
                p.is_active = False
                p.save()

        PlanUsage.objects.create(
            agent=admin,
            report=report,
            service="prefill",
            price=price
        )

        return Response({
            "success": True,
            "data": data
        })
        
        
from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework.response import Response

from .services.service import CibilService
from .permissions import IsAdminUserCustom


class AdminGenerateReportView(APIView):

    permission_classes = [IsAdminUserCustom]

    def post(self, request):

        result = CibilService.generate_report(
            request.user,
            request.data
        )

        if not result.get("success"):
            return Response(result, status=400)

        pdf = result.get("file")

        response = HttpResponse(
            pdf,
            content_type="application/pdf"
        )

        response["Content-Disposition"] = "attachment; filename=report.pdf"

        return response