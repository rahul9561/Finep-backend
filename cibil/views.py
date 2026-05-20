# cibil/views.py
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework import status
from django.core.files.base import ContentFile
from django.utils.timezone import now
import uuid
from wallet.services import wallet_debit
from django.db.models import F
from .serializers import CibilReportSerializer
from .services.service import CibilService ,get_dynamic_price
from .services.client import BureauAPIException ,BureauClient
from .models import AgentPlan ,AgentCibilPricing
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
import uuid
import logging
logger = logging.getLogger(__name__)



import uuid
from django.http import HttpResponse
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CibilReport
from .serializers import CibilReportSerializer


import uuid
from django.http import HttpResponse
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class GenerateCibilReportView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CibilReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        result = CibilService.generate_report(
            request.user,
            data
        )

        if not result.get("success"):
            return Response(result, status=400)

        pdf = result.get("file")

        if not pdf:
            return Response(
                {"success": False, "message": "PDF not generated"},
                status=500
            )

        filename = f"{uuid.uuid4()}.pdf"

        # ✅ DB SAVE
        # report = CibilReport.objects.create(
        #     agent=request.user,
        #     name=data.get("name"),
        #     mobile=data.get("mobile"),
        #     pan=data.get("pan"),
        #     report_type=data.get("report_type"),
        #     status="SUCCESS",
        # )

        # ✅ PDF SAVE
        # report.report_pdf.save(
        #     filename,
        #     ContentFile(pdf),
        #     save=True
        # )

        # ✅ RESPONSE
        response = HttpResponse(
            pdf,
            content_type="application/pdf"
        )

        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import CibilReport


class AgentCibilStatsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        reports = CibilReport.objects.filter(
            agent=request.user,
            status="SUCCESS"
        )

        total_reports = reports.count()

        today_reports = reports.filter(
            created_at__date=timezone.now().date()
        ).count()

        return Response({
            "total_generated": total_reports,
            "today_generated": today_reports
        })


# cibil/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from .models import RechargePlan
from .serializers import RechargePlanSerializer


class AdminRechargePlanViewSet(ModelViewSet):
    queryset = RechargePlan.objects.all().order_by("-created_at")
    serializer_class = RechargePlanSerializer
    permission_classes = [IsAdminUser]

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import RechargePlan
from .serializers import RechargePlanSerializer
from rest_framework.permissions import IsAuthenticated

class RechargePlanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # 🔥 only agent allowed
        if request.user.role != "agent":
            return Response({
                "message": "Only agents can view recharge plans"
            }, status=403)

        plans = RechargePlan.objects.filter(
            is_active=True
        ).order_by("amount")

        serializer = RechargePlanSerializer(
            plans,
            many=True
        )

        return Response({
            "status": True,
            "data": serializer.data
        })



from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from decimal import Decimal
# from wallet.models import Wallet, Transaction, WalletLedger
from .models import RechargePlan, AgentPlan




class PurchaseRechargePlanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        plan_id = request.data.get("plan_id")

        if not plan_id:
            return Response(
                {"success": False, "message": "plan_id is required"},
                status=400
            )

        try:

            plan = RechargePlan.objects.get(
                id=plan_id,
                is_active=True
            )

            amount = request.data.get("amount")

            # ---------------- FIXED ----------------

            if plan.plan_type == "FIXED":

                if not plan.amount or plan.amount <= 0:
                    return Response(
                        {
                            "success": False,
                            "message": "Plan amount not configured"
                        },
                        status=400
                    )

                recharge_amount = plan.amount

            # ---------------- RANGE ----------------

            elif plan.plan_type == "RANGE":

                if not amount:
                    return Response(
                        {
                            "success": False,
                            "message": "Amount is required"
                        },
                        status=400
                    )

                recharge_amount = Decimal(amount)

                if (
                    recharge_amount < plan.min_amount
                    or recharge_amount > plan.max_amount
                ):
                    return Response(
                        {
                            "success": False,
                            "message": f"Amount must be between {plan.min_amount} and {plan.max_amount}"
                        },
                        status=400
                    )

            # ===============================
            # WALLET DEBIT (SERVICE)
            # ===============================

            try:

                wallet_debit(
                    request.user,
                    recharge_amount,
                    service="CIBIL_PLAN",
                    note=f"Purchase Plan - {plan.title}"
                )

            except Exception as e:

                return Response(
                    {
                        "success": False,
                        "message": str(e)
                    },
                    status=400
                )

            # ===============================
            # CREATE AGENT PLAN
            # ===============================

            agent_plan = AgentPlan.objects.create(
                agent=request.user,
                plan=plan,
                remaining_balance=recharge_amount
            )

            return Response({
                "success": True,
                "message": "Plan activated successfully",
                "remaining_balance": agent_plan.remaining_balance
            })

        except RechargePlan.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Invalid plan"
                },
                status=400
            )


# cibil/views.py

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .models import CibilReport
from .serializers import RechargePlanSerializer
from rest_framework import serializers


class CibilReportHistorySerializer(serializers.ModelSerializer):

    download_url = serializers.SerializerMethodField()

    class Meta:
        model = CibilReport
        fields = [
            "id",
            "name",
            "mobile",
            "pan",
            "report_type",
            "status",
            "created_at",
            "download_url",   # ✅ add this
        ]

    def get_download_url(self, obj):

        request = self.context.get("request")

        if obj.report_pdf:
            return request.build_absolute_uri(obj.report_pdf.url)

        return None


class AgentCibilReportHistoryAPIView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = CibilReportHistorySerializer

    def get_queryset(self):
        return CibilReport.objects.filter(
            agent=self.request.user
        ).order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# cibil/views.py

from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models import Count


class AgentReportAnalyticsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        reports = CibilReport.objects.filter(
            agent=request.user,
            status="SUCCESS"
        )

        daily = (
            reports
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("-day")[:7]
        )

        monthly = (
            reports
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("-month")[:12]
        )

        yearly = (
            reports
            .annotate(year=TruncYear("created_at"))
            .values("year")
            .annotate(total=Count("id"))
            .order_by("-year")
        )

        return Response({
            "daily_reports": daily,
            "monthly_reports": monthly,
            "yearly_reports": yearly,
        })


from django.db.models import Sum
from .models import PlanUsage


class AgentServiceUsageAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        usages = PlanUsage.objects.filter(
            agent=request.user
        )

        service_stats = (
            usages.values("service")
            .annotate(
                total_reports=Count("id"),
                total_spent=Sum("price")
            )
        )

        return Response({
            "services": service_stats
        })


# cibil/views.py

import io
import zipfile
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import CibilReport


class DownloadAllReportsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        reports = CibilReport.objects.filter(
            agent=request.user,
            status="SUCCESS",
            report_pdf__isnull=False
        )

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:

            for report in reports:
                if report.report_pdf:

                    filename = f"{report.report_type}_{report.created_at.date()}.pdf"

                    zip_file.writestr(
                        filename,
                        report.report_pdf.read()
                    )

        zip_buffer.seek(0)

        response = HttpResponse(
            zip_buffer,
            content_type="application/zip"
        )

        response["Content-Disposition"] = "attachment; filename=all_cibil_reports.zip"

        return response


from django.utils import timezone


class DownloadReportsByDateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        filter_type = request.GET.get("type")

        reports = CibilReport.objects.filter(
            agent=request.user,
            status="SUCCESS"
        )

        today = timezone.now()

        if filter_type == "daily":
            reports = reports.filter(created_at__date=today.date())

        elif filter_type == "monthly":
            reports = reports.filter(
                created_at__month=today.month,
                created_at__year=today.year
            )

        elif filter_type == "yearly":
            reports = reports.filter(
                created_at__year=today.year
            )

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:

            for report in reports:

                if report.report_pdf:
                    filename = f"{report.report_type}_{report.id}.pdf"

                    zip_file.writestr(
                        filename,
                        report.report_pdf.read()
                    )

        zip_buffer.seek(0)

        response = HttpResponse(
            zip_buffer,
            content_type="application/zip"
        )

        response["Content-Disposition"] = "attachment; filename=reports.zip"

        return response


# cibil/views.py
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .models import AgentPlan
from .serializers import AgentPlanSerializer


from django.db.models import Sum

class AgentActivePlanView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        plans = AgentPlan.objects.filter(
            agent=request.user,
            is_active=True
        ).select_related("plan")

        serializer = AgentPlanSerializer(plans, many=True)

        total_balance = plans.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        return Response({
            "plans": serializer.data,
            "total_balance": total_balance
        })



from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
def prefill_mobile(request):

    mobile = request.data.get("mobile")
    name = request.data.get("name")

    if not mobile or not name:
        return Response({
            "success": False,
            "message": "Mobile and name required"
        })

    first_name = name.split(" ")[0]

    result = BureauClient.fetch_prefill(mobile, first_name)

    if result.get("status") != 200:
        return Response({
            "success": False,
            "message": result.get("message")
        })

    data = result.get("data", {})

    return Response({
        "success": True,
        "data": data
    })



from datetime import datetime

class DownloadReportsByRangeAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if not start_date or not end_date:
            return Response({
                "success": False,
                "message": "start_date and end_date are required (YYYY-MM-DD)"
            }, status=400)

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }, status=400)

        reports = CibilReport.objects.filter(
            agent=request.user,
            status="SUCCESS",
            created_at__date__range=[start_date, end_date]
        )

        if not reports.exists():
            return Response({
                "success": False,
                "message": "No reports found for this date range"
            }, status=404)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:

            for report in reports:

                if report.report_pdf:

                    filename = f"{report.report_type}_{report.created_at.date()}_{report.id}.pdf"

                    zip_file.writestr(
                        filename,
                        report.report_pdf.read()
                    )

        zip_buffer.seek(0)

        response = HttpResponse(
            zip_buffer,
            content_type="application/zip"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="reports_{start_date.date()}_to_{end_date.date()}.zip"'
        )

        return response


# admin 
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Count
from django.contrib.auth import get_user_model
from .models import CibilReport
from django.db import models

User = get_user_model()


class AdminUserReportStatsAPIView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):
        # ✅ FIRST define today
        today = now().date()

        users = (
            CibilReport.objects
            .values(
                "agent__id",
                "agent__username",
                "agent__email"
            )
            .annotate(
                total_reports=Count("id"),
                cibil=Count("id", filter=models.Q(report_type="cibil")),
                 # ✅ today per user
                today_reports=Count(
                    "id",
                    filter=Q(created_at__date=today)
                ),
                experian=Count("id", filter=models.Q(report_type="experian")),
                equifax=Count("id", filter=models.Q(report_type="equifax")),
                crif=Count("id", filter=models.Q(report_type="crif")),
            )
            .order_by("-total_reports")
        )
       

        return Response(users)



from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import CibilReport
from .serializers import AdminCibilReportSerializer


class AdminReportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminCibilReportListAPIView(ListAPIView):

    permission_classes = [IsAdminUser]
    serializer_class = AdminCibilReportSerializer
    pagination_class = AdminReportPagination

    def get_queryset(self):

        queryset = (
            CibilReport.objects
            .select_related("agent")
            .only(
                "id",
                "name",
                "mobile",
                "pan",
                "report_type",
                "status",
                "created_at",
                "report_pdf",
                "agent__username",
                "agent__email"
            )
        )

        user_id = self.request.GET.get("user_id")
        report_type = self.request.GET.get("report_type")
        search = self.request.GET.get("search")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if user_id:
            queryset = queryset.filter(agent_id=user_id)

        if report_type:
            queryset = queryset.filter(report_type=report_type)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(mobile__icontains=search) |
                Q(pan__icontains=search)
            )

        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )

        return queryset.order_by("-created_at")
    
    
    
    
    
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def prefill_check(request):

    # agent = request.user
    user = request.user

    if user.role == "customer":
        agent = user.created_by
    else:
        agent = user

    mobile = request.data.get("mobile")
    name = request.data.get("name")

    if not mobile or not name:
        return Response({
            "success": False,
            "message": "Mobile and name required"
        })

    # =========================
    # PLAN CHECK
    # =========================

    agent_plans = AgentPlan.objects.select_for_update().filter(
        agent=agent,
        is_active=True
    ).order_by("created_at")

    if not agent_plans.exists():

        return Response({
            "success": False,
            "message": "Please recharge plan"
        })


    active_plan = agent_plans.last()
    plan = active_plan.plan
    selling_price = get_dynamic_price(user, "prefill")
    plan_price = plan.prefill_price


    total_balance = agent_plans.aggregate(
        total=Sum("remaining_balance")
    )["total"] or 0


    # if total_balance < price:
    if total_balance < plan_price:

        return Response({
            "success": False,
            "message": "Insufficient balance"
        })
    from wallet.services import wallet_debit

    if user.role == "customer":
        wallet_debit(
            user=user,
            amount=selling_price,
            service="prefill",
            note="Prefill check"
        )
        
    result = BureauClient.fetch_prefill(
        mobile,
        name
    )
        
    if result.get("status") != 200:

        from wallet.services import wallet_credit

        if user.role == "customer":
            wallet_credit(
                user=user,
                amount=selling_price,
                service="prefill",
                note="Refund (Prefill failed)"
            )

   

  
    if result.get("status") != 200:

        api_msg = result.get("message", "")

        if "service_error" in api_msg.lower():
            message = "Number not linked with PAN / No credit record found"
        else:
            message = api_msg

        return Response({
            "success": False,
            "message": message
        })


    data = result.get("data", {})
    print("data-list",data)
    pan_list = data.get("pan_number") or []
    pan = pan_list[0] if pan_list else None

    # ✅ IMPORTANT FIX
    if not pan:
        return Response({
            "success": False,
            "message": "PAN not found for this mobile"
        })

    report = CibilReport.objects.create(
        agent=agent,
        name=data.get("name") or name,
        mobile=mobile,
        pan=pan, 
        report_type="prefill",
        status="SUCCESS"
    )


    # =========================
    # DEDUCT BALANCE (FIFO)
    # =========================

    # remaining_price = price
    # remaining_price = plan.prefill_price   ✅
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


    # =========================
    # SAVE USAGE
    # =========================

    profit = max(selling_price - plan_price, 0)

    PlanUsage.objects.create(
        agent=agent,
        customer=user if user.role == "customer" else None,  # ✅ ADD THIS
        report=report,
        service="prefill",
        price=selling_price,
        status="SUCCESS",
        profit=profit, 
        reference_id = f"PREFILL-{uuid.uuid4().hex[:10]}"
    )


    # =========================
    # RESPONSE
    # =========================

    data = result.get("data", {})
    return Response({
            "success": True,
            "data": {
                "name": data.get("name"),
                "mobile": mobile,
                "pan": pan,
                "gender": data.get("gender"),
                "dob": data.get("dob"),
                "email": (data.get("emails") or [None])[0],
                "address": (data.get("addresses") or [None])[0],
            },
            "report_types": [
                {"label": "CIBIL", "value": "cibil"},
                {"label": "Experian", "value": "experian"},
                {"label": "Equifax", "value": "equifax"},
                {"label": "CRIF", "value": "crif"},
            ]
        })
    
    
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from rest_framework.response import Response
from .services.service import CibilService



class GenerateReportAfterPrefillView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        result = CibilService.generate_report(
            request.user,
            request.data
        )

        if not result.get("success"):
            return Response(result, status=400)

        pdf = result.get("file")

        filename = f"{uuid.uuid4()}.pdf"

        report = CibilReport.objects.create(
            agent=request.user,
            name=request.data.get("name"),
            mobile=request.data.get("mobile"),
            pan=request.data.get("pan"),
            report_type=request.data.get("report_type"),
            status="SUCCESS",
        )

        report.report_pdf.save(
            filename,
            ContentFile(pdf),
            save=True
        )

        response = HttpResponse(
            pdf,
            content_type="application/pdf"
        )

        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
    
    
    
    
    
# cibil/views.py

class SetCibilPricingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.role != "agent":
            return Response({"message": "Only agent allowed"}, status=403)

        customer_id = request.data.get("customer_id")

        customer = None
        if customer_id:
            customer = User.objects.filter(
                id=customer_id,
                created_by=request.user
            ).first()

            if not customer:
                return Response({"message": "Customer not found"}, status=404)

      
        services = [choice[0] for choice in AgentCibilPricing.SERVICE_CHOICES]

        result = []

        for service in services:

            price = request.data.get(f"{service}_price")

            if price is None:
                continue

            obj, _ = AgentCibilPricing.objects.update_or_create(
                agent=request.user,
                customer=customer,
                service=service,
                defaults={"price": price}   # ✅ FIX
            )

            result.append({
                "service": service,
                "price": obj.price
            })

        return Response({
            "status": True,
            "data": result,
            "customer": customer.username if customer else "ALL"
        })
        
        
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import PlanUsage, CibilReport, AgentPlan


class AgentDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        # =========================
        # 📊 TOTAL REPORTS
        # =========================
        total_reports = CibilReport.objects.filter(
            agent=user,
            status="SUCCESS"
        ).count()

        # =========================
        # 💰 TOTAL EARNINGS (PROFIT)
        # =========================
        earnings = PlanUsage.objects.filter(
            agent=user
        ).aggregate(
            total_profit=Sum("profit"),
            total_revenue=Sum("price")
        )

        total_profit = earnings["total_profit"] or 0
        total_revenue = earnings["total_revenue"] or 0

        # =========================
        # 💳 BALANCE
        # =========================
        balance = AgentPlan.objects.filter(
            agent=user,
            is_active=True
        ).aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        return Response({
            "status": True,
            "data": {
                "total_reports": total_reports,
                "total_earnings": total_profit,
                "total_revenue": total_revenue,
                "balance": balance
            }
        })
        
        
# class CustomerPricingAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         user = request.user
#         agent = user.created_by if user.role == "customer" else user

#         SERVICES = [
#             "prefill",
#             "cibil",
#             "experian",
#             "crif",
#             "equifax",
#             "aadhaar",
#             "pan",
#             "gst",
#             "bank",
#             "msme",
#             "rc",
#             "electricity",
#         ]

#         # 🔥 correct mapping
#         SERVICE_MAP = {
#             "pan": "pan_verify",
#             "gst": "gst_verify",
#             "bank": "bank_verify",
#             "aadhaar": "aadhaar_verify",  # only if supported
#         }

#         data = []

#         for service in SERVICES:

#             mapped_service = SERVICE_MAP.get(service, service)

#             price = 0

#             try:
#                 price = get_dynamic_price(user, mapped_service)
#             except Exception:
#                 price = 0

#             # 🔥 skip unknown services (OPTIONAL)
#             if price == 0:
#                 continue

#             data.append({
#                 "service": service,
#                 "price": price
#             })

#         return Response({
#             "status": True,
#             "count": len(data),
#             "data": data
#         })

# class CustomerPricingAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         user = request.user
#         agent = user.created_by if user.role == "customer" else user

#         SERVICES = [
#             "prefill",
#             "cibil",
#             "experian",
#             "crif",
#             "equifax",
#             "aadhaar",
#             "pan",
#             "gst",
#             "bank",
#             "cibil_advanced",
#             "only_score",
#             "msme",
#             "rc",
#             "electricity",
#             "leegality_esign",
#             "mobile360",
#         ]

#         SERVICE_MAP = {
#             "pan": "pan_verify",
#             "gst": "gst_verify",
#             "bank": "bank_verify",
#             "aadhaar": "aadhaar_verify",
#         }

#         data = []

#         for service in SERVICES:

#             mapped_service = SERVICE_MAP.get(service, service)

#             # 🔥 ONLY AGENT-SET PRICE
#             custom_price = AgentCibilPricing.objects.filter(
#                 agent=agent,
#                 customer=user if user.role == "customer" else None,
#                 service=mapped_service
#             ).order_by("-id").first()

#             if not custom_price:
#                 continue

#             data.append({
#                 "service": service,
#                 "price": custom_price.price,
#                 "is_custom": True
#             })

#         return Response({
#             "status": True,
#             "count": len(data),
#             "data": data
#         })

class CustomerPricingAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        agent = (
            user.created_by
            if user.role == "customer"
            else user
        )

        SERVICES = [
            "prefill",
            "cibil",
            "experian",
            "crif",
            "equifax",
            "aadhaar",
            "pan",
            "gst",
            "bank",
            "cibil_advanced",
            "only_score",
            "msme",
            "rc",
            "electricity",
            "leegality_esign",
            "mobile360",
        ]

        SERVICE_MAP = {
            "pan": "pan_verify",
            "gst": "gst_verify",
            "bank": "bank_verify",
            "aadhaar": "aadhaar_verify",
        }

        data = []

        for service in SERVICES:

            mapped_service = SERVICE_MAP.get(
                service,
                service
            )

            custom_price = (
                AgentCibilPricing.objects.filter(
                    agent=agent,
                    customer=(
                        user
                        if user.role == "customer"
                        else None
                    ),
                    service=mapped_service
                )
                .order_by("-id")
                .first()
            )

            if not custom_price:
                continue

            # ====================================
            # MAIN SERVICE
            # ====================================

            data.append({
                "service": service,
                "price": custom_price.price,
                "is_custom": True
            })

            # ====================================
            # ADD CIBIL JSON AUTOMATICALLY
            # ====================================

            if service == "cibil":

                data.append({
                    "service": "cibil_json",
                    "price": custom_price.price,
                    "is_custom": True
                })

        return Response({
            "status": True,
            "count": len(data),
            "data": data
        })
        
        

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services.surepassservices import SureCibilService
from cibil.models import CibilReport


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def surepassgenerate_cibil_report(request):

#     agent = request.user
#     data = request.data

#     pan = (data.get("pan") or "").upper().strip()
#     report_type = data.get("report_type")

#     result = SureCibilService.generate_report(agent, data)

#     # ❌ FAILED
#     if not result.get("success"):
#         return Response(
#             {
#                 "success": False,
#                 "message": result.get("message")
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     # ✅ FETCH LATEST REPORT
#     report = CibilReport.objects.filter(
#         agent=agent,
#         pan=pan,
#         report_type=report_type,
#         status="SUCCESS"
#     ).order_by("-created_at").first()

#     if not report or not report.report_pdf:
#         return Response(
#             {
#                 "success": False,
#                 "message": "Report generated but PDF not found"
#             },
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     # 🔥 MAIN FIX (IMPORTANT)
#     pdf_url = request.build_absolute_uri(report.report_pdf.url)

#     return Response(
#         {
#             "success": True,
#             "message": "Report generated successfully",
#             "pdf_url": pdf_url
#         },
#         status=status.HTTP_200_OK
#     )

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services.surepassservices import SureCibilService
from cibil.models import CibilReport


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def surepassgenerate_cibil_report(request):

    user = request.user
    data = request.data

    pan = (data.get("pan") or "").upper().strip()
    report_type = data.get("report_type")

    # =========================
    # GENERATE REPORT
    # =========================
    result = SureCibilService.generate_report(user, data)

    # ❌ FAILED
    if not result.get("success"):
        return Response(
            {
                "success": False,
                "message": result.get("message")
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =========================
    # FETCH LATEST REPORT
    # =========================
    report = CibilReport.objects.filter(
        agent=user if not hasattr(user, "created_by") else user.created_by,
        pan=pan,
        report_type=report_type,
        status="SUCCESS"
    ).order_by("-created_at").first()

    # ❌ REPORT NOT FOUND
    if not report:
        return Response(
            {
                "success": False,
                "message": "Report not found"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # =========================
    # CASE 1: PDF AVAILABLE
    # =========================
    if report.report_pdf:
        pdf_url = request.build_absolute_uri(report.report_pdf.url)

        return Response(
            {
                "success": True,
                "message": "Report generated successfully",
                "pdf_url": pdf_url
            },
            status=status.HTTP_200_OK
        )

    # =========================
    # CASE 2: PDF NOT SAVED (EXPERIAN SAFE CASE)
    # =========================
    return Response(
        {
            "success": True,
            "message": "Report generated successfully (PDF processing or unavailable)",
            "pdf_url": None
        },
        status=status.HTTP_200_OK
    )
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from .services.surepassservices import SureCibilService
# from cibil.models import CibilReport
# import logging

# logger = logging.getLogger(__name__)


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def surepassgenerate_cibil_report(request):

#     agent = request.user
#     data = request.data

#     pan = (data.get("pan") or "").upper().strip()
#     report_type = data.get("report_type")

#     logger.info(f"[API INPUT] agent={agent}, data={data}")

#     result = SureCibilService.generate_report(agent, data)

#     # 🔥 DEBUG FULL RESULT
#     logger.error(f"[SERVICE RESULT] {result}")

#     # ❌ FAILED
#     if not result.get("success"):
#         return Response(
#             {
#                 "success": False,
#                 "message": result.get("message"),

#                 # 🔥 DEBUG ADDITIONS
#                 "debug": {
#                     "report_type": report_type,
#                     "pan": pan,
#                     "service_raw": result.get("raw"),   # full API response
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     # ✅ FETCH LATEST REPORT
#     report = CibilReport.objects.filter(
#         agent=agent,
#         pan=pan,
#         report_type=report_type,
#         status="SUCCESS"
#     ).order_by("-created_at").first()

#     if not report or not report.report_pdf:
#         logger.error("[PDF ERROR] Report exists but file missing")

#         return Response(
#             {
#                 "success": False,
#                 "message": "Report generated but PDF not found",
#                 "debug": {
#                     "report_found": bool(report),
#                     "has_pdf": bool(report and report.report_pdf)
#                 }
#             },
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     # 🔥 MAIN FIX
#     pdf_url = request.build_absolute_uri(report.report_pdf.url)

#     logger.info(f"[SUCCESS] PDF URL: {pdf_url}")

#     return Response(
#         {
#             "success": True,
#             "message": "Report generated successfully",
#             "pdf_url": pdf_url
#         },
#         status=status.HTTP_200_OK
#     )

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services.BeFiScServices import BeFicCibilService
from cibil.models import CibilReport


import re
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


def handle_cibil(request, report_type):

    pan = (request.data.get("pan") or "").upper().strip()
    mobile = str(request.data.get("mobile") or "").strip()

    # ✅ PAN Validation
    if not pan:
        return Response(
            {"success": False, "message": "PAN required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    pan_regex = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"

    if not re.match(pan_regex, pan):
        return Response(
            {"success": False, "message": "Invalid PAN number"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Mobile Validation
    if not mobile:
        return Response(
            {"success": False, "message": "Mobile required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(mobile) != 10 or not mobile.isdigit():
        return Response(
            {"success": False, "message": "Invalid mobile number"},
            status=status.HTTP_400_BAD_REQUEST
        )

    data = {
        "pan": pan,
        "mobile": mobile,
        "report_type": report_type,
    }

    # ✅ Name required only for full report
    if report_type == "cibil_advanced":
        name = (request.data.get("name") or "").strip()

        if not name:
            return Response(
                {"success": False, "message": "Name required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data["name"] = name

    result = BeFicCibilService.generate_report(request.user, data)

    if not result.get("success"):
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_cibil_report(request):

    print("========== REQUEST DATA ==========")
    print(request.data)
    print("==================================")

    response = handle_cibil(request, "cibil_advanced")

    print("========== RESPONSE ==========")
    print(response.data)
    print("==================================")

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def only_score_check(request):
    return handle_cibil(request, "only_score")




# api price views for admin/agent
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from cibil.models import AgentCibilPricing


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customer_pricing(request):

    agent = request.user

    if agent.role != "agent":
        return Response({
            "success": False,
            "message": "Only agent allowed"
        }, status=403)

    pricings = AgentCibilPricing.objects.filter(
        agent=agent
    ).select_related("customer")

    data = []

    for item in pricings:
        data.append({
            "id": item.id,
            "customer_id": item.customer.id if item.customer else None,
            "customer_name": item.customer.username if item.customer else "Default",
            "customer_code": item.customer.user_code if item.customer else None,
            "service": item.service,
            "price": str(item.price),
            "created_at": item.created_at,
        })

    return Response({
        "success": True,
        "count": len(data),
        "data": data
    })
    
    
    
# views.py
# from decimal import Decimal

# import requests

# from django.conf import settings
# from django.core.files.base import ContentFile

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# from .models import (
#     CibilReport,
#     AgentPlan,
#     PlanUsage,
#     AgentCibilPricing
# )


# class GenerateCibilReportJsonView(APIView):

#     def post(self, request):

#         try:

#             # =========================================
#             # LOGIN USER = AGENT
#             # =========================================

#             agent = request.user

#             # =========================================
#             # REQUEST DATA
#             # =========================================

#             name = request.data.get("name")
#             mobile = request.data.get("mobile")
#             pan_card = request.data.get("pan_card")
#             gender = request.data.get("gender")
#             report_type = request.data.get(
#                 "report_type",
#                 "cibil"
#             )

#             # =========================================
#             # AGENT ACTIVE PLAN
#             # =========================================

#             agent_plan = AgentPlan.objects.filter(
#                 agent=agent,
#                 is_active=True
#             ).select_related("plan").first()

#             if not agent_plan:

#                 return Response(
#                     {
#                         "status": False,
#                         "message": "No active plan found"
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # =========================================
#             # ADMIN COST PRICE
#             # =========================================

#             plan = agent_plan.plan

#             SERVICE_PRICE_MAP = {

#                 "cibil": plan.cibil_price,

#                 "experian": plan.experian_price,

#                 "equifax": plan.equifax_price,

#                 "crif": plan.crif_price,

#                 "prefill": plan.prefill_price,

#                 "aadhaar_verify": plan.aadhaar_price,

#                 "pan_verify": plan.pan_verify_price,

#                 "gst_verify": plan.gst_verify_price,

#                 "bank_verify": plan.bank_verify_price,

#                 "cibil_advanced":
#                     plan.cibil_advanced_price,

#                 "only_score":
#                     plan.only_score_price,

#                 "mobile360":
#                     plan.mobile360_price,

#                 "leegality_esign":
#                     plan.leegality_esign_price,
#             }

#             agent_cost_price = Decimal(
#                 SERVICE_PRICE_MAP.get(
#                     report_type,
#                     0
#                 )
#             )

#             # =========================================
#             # AGENT SELL PRICE
#             # =========================================

#             customer_price = agent_cost_price

#             # agent_price = AgentCibilPricing.objects.filter(
#             #     agent=agent,
#             #     customer__isnull=True,
#             #     service=report_type
#             # ).first()
#             pricing_service = report_type

#             if report_type == "cibil_json":
#                 pricing_service = "cibil"

#             agent_price = AgentCibilPricing.objects.filter(
#                 agent=agent,
#                 customer__isnull=True,
#                 service=pricing_service
#             ).first()

#             if agent_price:

#                 customer_price = Decimal(
#                     agent_price.price
#                 )

#             # =========================================
#             # CHECK BALANCE
#             # =========================================

#             if (
#                 agent_plan.remaining_balance
#                 < agent_cost_price
#             ):

#                 return Response(
#                     {
#                         "status": False,
#                         "message":
#                             "Insufficient balance"
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # =========================================
#             # CREATE REPORT
#             # =========================================

#             report = CibilReport.objects.create(
#                 agent=agent,
#                 name=name,
#                 mobile=mobile,
#                 pan=pan_card,
#                 report_type=report_type,
#                 status="PENDING"
#             )

#             # =========================================
#             # VERIFYAL API
#             # =========================================

#             url = (
#                 "https://console.verifyal.com/"
#                 "vendor-api/generate-report-data"
#             )

#             payload = {
#                 "name": name,
#                 "mobile": mobile,
#                 "pan_card": pan_card,
#                 "report_type": report_type,
#                 "gender": gender,
#                 "consent": "Y"
#             }

#             headers = {
#                 "Token": settings.CIBIL_TOKEN,
#                 "API-KEY": settings.CIBIL_API_KEY
#             }

#             response = requests.post(
#                 url,
#                 data=payload,
#                 headers=headers
#             )

#             response_data = response.json()

#             print(response_data)

#             # =========================================
#             # FAILED
#             # =========================================

#             if response.status_code != 200:

#                 report.status = "FAILED"

#                 report.response_message = str(
#                     response_data
#                 )

#                 report.save()

#                 return Response(
#                     {
#                         "status": False,
#                         "message": response_data
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # =========================================
#             # SAVE PDF
#             # =========================================

#             pdf_url = response_data.get("pdf_url")

#             if pdf_url:

#                 pdf_response = requests.get(
#                     pdf_url
#                 )

#                 if pdf_response.status_code == 200:

#                     pdf_name = f"{report.id}.pdf"

#                     report.report_pdf.save(
#                         pdf_name,
#                         ContentFile(
#                             pdf_response.content
#                         ),
#                         save=False
#                     )

#             # =========================================
#             # SUCCESS REPORT
#             # =========================================

#             report.status = "SUCCESS"

#             report.response_message = str(
#                 response_data
#             )

#             report.save()

#             # =========================================
#             # DEDUCT AGENT BALANCE
#             # =========================================

#             agent_plan.remaining_balance -= (
#                 agent_cost_price
#             )

#             agent_plan.save()

#             # =========================================
#             # PROFIT
#             # =========================================

#             profit = (
#                 customer_price
#                 - agent_cost_price
#             )

#             # =========================================
#             # SAVE USAGE
#             # =========================================

#             PlanUsage.objects.create(
#                 agent=agent,
#                 report=report,
#                 service=report_type,
#                 status="SUCCESS",
#                 cost_price=agent_cost_price,
#                 price=customer_price,
#                 profit=profit,
#                 reference_id=str(report.id)
#             )

#             # =========================================
#             # RESPONSE
#             # =========================================

#             return Response(
#                 {
#                     "status": True,

#                     "message":
#                         "Report Generated Successfully",

#                     "report_id":
#                         str(report.id),

#                     "agent_cost_price":
#                         str(agent_cost_price),

#                     "customer_price":
#                         str(customer_price),

#                     "profit":
#                         str(profit),

#                     "remaining_balance":
#                         str(
#                             agent_plan.remaining_balance
#                         ),

#                     "pdf": (
#                         report.report_pdf.url
#                         if report.report_pdf
#                         else None
#                     ),

#                     "data": response_data
#                 },
#                 status=status.HTTP_200_OK
#             )

#         except Exception as e:

#             return Response(
#                 {
#                     "status": False,
#                     "message": str(e)
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

# from decimal import Decimal
# import uuid

# import requests

# from django.conf import settings
# from django.core.files.base import ContentFile
# from django.db import transaction

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# from wallet.models import (
#     Wallet,
#     WalletTransaction,
#     WalletLedger
# )

# from .models import (
#     CibilReport,
#     AgentPlan,
#     PlanUsage,
#     AgentCibilPricing
# )


# class GenerateCibilReportJsonView(APIView):

#     def post(self, request):

#         try:

#             with transaction.atomic():

#                 # =========================================
#                 # AGENT + CUSTOMER
#                 # =========================================

#                 customer = request.user

#                 agent = (
#                     request.user.created_by
#                     if request.user.role == "customer"
#                     else request.user
#                 )

#                 print("CUSTOMER:", customer)
#                 print("AGENT:", agent)

#                 # =========================================
#                 # REQUEST DATA
#                 # =========================================

#                 name = request.data.get("name")

#                 mobile = request.data.get("mobile")

#                 pan_card = request.data.get("pan_card")

#                 gender = request.data.get("gender")

#                 report_type = request.data.get(
#                     "report_type",
#                     "cibil"
#                 )

#                 # =========================================
#                 # AGENT ACTIVE PLAN
#                 # =========================================

#                 agent_plan = AgentPlan.objects.filter(
#                     agent=agent,
#                     is_active=True
#                 ).select_related("plan").first()

#                 if not agent_plan:

#                     return Response(
#                         {
#                             "status": False,
#                             "message":
#                                 "No active plan found"
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # =========================================
#                 # PLAN
#                 # =========================================

#                 plan = agent_plan.plan

#                 SERVICE_PRICE_MAP = {

#                     "cibil":
#                         plan.cibil_price,

#                     "experian":
#                         plan.experian_price,

#                     "equifax":
#                         plan.equifax_price,

#                     "crif":
#                         plan.crif_price,

#                     "prefill":
#                         plan.prefill_price,

#                     "aadhaar_verify":
#                         plan.aadhaar_price,

#                     "pan_verify":
#                         plan.pan_verify_price,

#                     "gst_verify":
#                         plan.gst_verify_price,

#                     "bank_verify":
#                         plan.bank_verify_price,

#                     "cibil_advanced":
#                         plan.cibil_advanced_price,

#                     "only_score":
#                         plan.only_score_price,

#                     "mobile360":
#                         plan.mobile360_price,

#                     "leegality_esign":
#                         plan.leegality_esign_price,
#                 }

#                 # =========================================
#                 # AGENT COST PRICE
#                 # =========================================

#                 agent_cost_price = Decimal(
#                     SERVICE_PRICE_MAP.get(
#                         report_type,
#                         0
#                     )
#                 )

#                 # =========================================
#                 # CUSTOMER PRICE
#                 # =========================================

#                 customer_price = agent_cost_price

#                 pricing_service = report_type

#                 if report_type == "cibil_json":

#                     pricing_service = "cibil"

#                 agent_price = AgentCibilPricing.objects.filter(
#                     agent=agent,
#                     customer__isnull=True,
#                     service=pricing_service
#                 ).first()

#                 if agent_price:

#                     customer_price = Decimal(
#                         agent_price.price
#                     )

#                 # =========================================
#                 # CUSTOMER WALLET
#                 # =========================================

#                 customer_wallet = Wallet.objects.filter(
#                     user=customer
#                 ).first()

#                 if not customer_wallet:

#                     return Response(
#                         {
#                             "status": False,
#                             "message":
#                                 "Customer wallet not found"
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # =========================================
#                 # CHECK CUSTOMER BALANCE
#                 # =========================================

#                 if (
#                     customer_wallet.balance
#                     < customer_price
#                 ):

#                     return Response(
#                         {
#                             "status": False,
#                             "message":
#                                 "Insufficient customer wallet balance"
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # =========================================
#                 # CHECK AGENT PLAN BALANCE
#                 # =========================================

#                 if (
#                     agent_plan.remaining_balance
#                     < agent_cost_price
#                 ):

#                     return Response(
#                         {
#                             "status": False,
#                             "message":
#                                 "Agent plan balance insufficient"
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # =========================================
#                 # CREATE REPORT
#                 # =========================================

#                 report = CibilReport.objects.create(
#                     agent=agent,
#                     name=name,
#                     mobile=mobile,
#                     pan=pan_card,
#                     report_type=report_type,
#                     status="PENDING"
#                 )

#                 # =========================================
#                 # VERIFYAL API
#                 # =========================================

#                 url = (
#                     "https://console.verifyal.com/"
#                     "vendor-api/generate-report-data"
#                 )

#                 payload = {
#                     "name": name,
#                     "mobile": mobile,
#                     "pan_card": pan_card,
#                     "report_type": report_type,
#                     "gender": gender,
#                     "consent": "Y"
#                 }

#                 headers = {
#                     "Token": settings.CIBIL_TOKEN,
#                     "API-KEY": settings.CIBIL_API_KEY
#                 }

#                 response = requests.post(
#                     url,
#                     data=payload,
#                     headers=headers
#                 )

#                 response_data = response.json()

#                 print(response_data)

#                 # =========================================
#                 # FAILED
#                 # =========================================

#                 if response.status_code != 200:

#                     report.status = "FAILED"

#                     report.response_message = str(
#                         response_data
#                     )

#                     report.save()

#                     return Response(
#                         {
#                             "status": False,
#                             "message": response_data
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # =========================================
#                 # SAVE PDF
#                 # =========================================

#                 pdf_url = response_data.get("pdf_url")

#                 if pdf_url:

#                     pdf_response = requests.get(
#                         pdf_url
#                     )

#                     if pdf_response.status_code == 200:

#                         pdf_name = f"{report.id}.pdf"

#                         report.report_pdf.save(
#                             pdf_name,
#                             ContentFile(
#                                 pdf_response.content
#                             ),
#                             save=False
#                         )

#                 # =========================================
#                 # SUCCESS REPORT
#                 # =========================================

#                 report.status = "SUCCESS"

#                 report.response_message = str(
#                     response_data
#                 )

#                 report.save()

#                 # =========================================
#                 # CUSTOMER WALLET DEDUCTION
#                 # =========================================

#                 opening_balance = (
#                     customer_wallet.balance
#                 )

#                 closing_balance = (
#                     opening_balance - customer_price
#                 )

#                 customer_wallet.balance = (
#                     closing_balance
#                 )

#                 customer_wallet.save()

#                 # =========================================
#                 # WALLET TRANSACTION
#                 # =========================================

#                 wallet_txn = WalletTransaction.objects.create(

#                     user=customer,

#                     reference_id=str(
#                         uuid.uuid4()
#                     ),

#                     amount=customer_price,

#                     txn_type="debit",

#                     service=report_type,

#                     narration=(
#                         f"{report_type} report generated"
#                     )
#                 )

#                 # =========================================
#                 # WALLET LEDGER
#                 # =========================================

#                 WalletLedger.objects.create(

#                     wallet=customer_wallet,

#                     transaction=wallet_txn,

#                     opening_balance=opening_balance,

#                     amount=customer_price,

#                     closing_balance=closing_balance,

#                     entry_type="debit"
#                 )

#                 # =========================================
#                 # AGENT PLAN DEDUCT
#                 # =========================================

#                 agent_plan.remaining_balance -= (
#                     agent_cost_price
#                 )

#                 agent_plan.save()

#                 # =========================================
#                 # PROFIT
#                 # =========================================

#                 profit = (
#                     customer_price
#                     - agent_cost_price
#                 )

#                 # =========================================
#                 # SAVE USAGE
#                 # =========================================

#                 PlanUsage.objects.create(

#                     agent=agent,

#                     report=report,

#                     service=report_type,

#                     status="SUCCESS",

#                     cost_price=agent_cost_price,

#                     price=customer_price,

#                     profit=profit,

#                     reference_id=str(report.id)
#                 )

#                 # =========================================
#                 # RESPONSE
#                 # =========================================

#                 return Response(
#                     {
#                         "status": True,

#                         "message":
#                             "Report Generated Successfully",

#                         "report_id":
#                             str(report.id),

#                         "agent_cost_price":
#                             str(agent_cost_price),

#                         "customer_price":
#                             str(customer_price),

#                         "profit":
#                             str(profit),

#                         "remaining_balance":
#                             str(
#                                 agent_plan.remaining_balance
#                             ),

#                         "customer_wallet_balance":
#                             str(
#                                 customer_wallet.balance
#                             ),

#                         "pdf": (
#                             report.report_pdf.url
#                             if report.report_pdf
#                             else None
#                         ),

#                         "data": response_data
#                     },
#                     status=status.HTTP_200_OK
#                 )

#         except Exception as e:

#             return Response(
#                 {
#                     "status": False,
#                     "message": str(e)
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )



from decimal import Decimal
import uuid

import requests

from django.conf import settings
from django.core.files.base import ContentFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from wallet.models import (
    Wallet,
    WalletTransaction,
    WalletLedger
)

from .models import (
    CibilReport,
    AgentPlan,
    PlanUsage,
    AgentCibilPricing
)


class GenerateCibilReportJsonView(APIView):

    def post(self, request):

        report = None

        try:

            # =========================================
            # AGENT + CUSTOMER
            # =========================================

            customer = request.user

            agent = (
                request.user.created_by
                if request.user.role == "customer"
                else request.user
            )

            print("CUSTOMER:", customer)
            print("AGENT:", agent)

            # =========================================
            # REQUEST DATA
            # =========================================

            name = request.data.get("name")

            mobile = request.data.get("mobile")

            pan_card = request.data.get("pan_card")

            gender = request.data.get("gender")

            report_type = request.data.get(
                "report_type",
                "cibil"
            )

            # =========================================
            # AGENT ACTIVE PLAN
            # =========================================

            agent_plan = AgentPlan.objects.filter(
                agent=agent,
                is_active=True
            ).select_related("plan").first()

            if not agent_plan:

                return Response(
                    {
                        "status": False,
                        "message":
                            "No active plan found"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =========================================
            # PLAN
            # =========================================

            plan = agent_plan.plan

            SERVICE_PRICE_MAP = {

                "cibil":
                    plan.cibil_price,

                "experian":
                    plan.experian_price,

                "equifax":
                    plan.equifax_price,

                "crif":
                    plan.crif_price,

                "prefill":
                    plan.prefill_price,

                "aadhaar_verify":
                    plan.aadhaar_price,

                "pan_verify":
                    plan.pan_verify_price,

                "gst_verify":
                    plan.gst_verify_price,

                "bank_verify":
                    plan.bank_verify_price,

                "cibil_advanced":
                    plan.cibil_advanced_price,

                "only_score":
                    plan.only_score_price,

                "mobile360":
                    plan.mobile360_price,

                "leegality_esign":
                    plan.leegality_esign_price,
            }

            # =========================================
            # AGENT COST PRICE
            # =========================================

            agent_cost_price = Decimal(
                SERVICE_PRICE_MAP.get(
                    report_type,
                    0
                )
            )

            # =========================================
            # CUSTOMER PRICE
            # =========================================

            customer_price = agent_cost_price

            pricing_service = report_type

            if report_type == "cibil_json":

                pricing_service = "cibil"

            agent_price = AgentCibilPricing.objects.filter(
                agent=agent,
                customer__isnull=True,
                service=pricing_service
            ).first()

            if agent_price:

                customer_price = Decimal(
                    agent_price.price
                )

            # =========================================
            # CUSTOMER WALLET
            # =========================================

            customer_wallet = Wallet.objects.filter(
                user=customer
            ).first()

            if not customer_wallet:

                return Response(
                    {
                        "status": False,
                        "message":
                            "Customer wallet not found"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =========================================
            # CHECK CUSTOMER BALANCE
            # =========================================

            if (
                customer_wallet.balance
                < customer_price
            ):

                return Response(
                    {
                        "status": False,
                        "message":
                            "Insufficient customer wallet balance"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =========================================
            # CHECK AGENT PLAN BALANCE
            # =========================================

            if (
                agent_plan.remaining_balance
                < agent_cost_price
            ):

                return Response(
                    {
                        "status": False,
                        "message":
                            "Agent plan balance insufficient"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =========================================
            # CREATE REPORT
            # =========================================

            report = CibilReport.objects.create(
                agent=agent,
                name=name,
                mobile=mobile,
                pan=pan_card,
                report_type=report_type,
                status="PENDING"
            )

            # =========================================
            # VERIFYAL API
            # =========================================

            url = (
                "https://console.verifyal.com/"
                "vendor-api/generate-report-data"
            )

            payload = {
                "name": name,
                "mobile": mobile,
                "pan_card": pan_card,
                "report_type": report_type,
                "gender": gender,
                "consent": "Y"
            }

            headers = {
                "Token": settings.CIBIL_TOKEN,
                "API-KEY": settings.CIBIL_API_KEY
            }

            response = requests.post(
                url,
                data=payload,
                headers=headers
            )

            response_data = response.json()
            api_message = str(

                response_data.get("message", "")

            ).lower()

            print(response_data)

            # =========================================
            # FAILED
            # =========================================

            if (

                response.status_code != 200

                or response_data.get("success") is False

                or response_data.get("status") in [False, 0, "0",400,"400"]
                
                or "no credit history" in api_message

                or "failed" in api_message

                or response_data.get("data") == []

            ):

                report.status = "FAILED"

                report.response_message = str(
                    response_data
                )

                report.save()

                # =====================================
                # SAVE FAILED USAGE
                # =====================================

                PlanUsage.objects.create(

                    agent=agent,

                    customer=customer,

                    report=report,

                    service=report_type,

                    status="FAILED",

                    cost_price=agent_cost_price,

                    price=customer_price,

                    profit=Decimal("0.00"),

                    reference_id=str(report.id)

                )

                return Response(
                    {
                        "status": False,
                        "message": response_data
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # =========================================
            # SAVE PDF
            # =========================================

            pdf_url = response_data.get("pdf_url")

            if pdf_url:

                pdf_response = requests.get(
                    pdf_url
                )

                if pdf_response.status_code == 200:

                    pdf_name = f"{report.id}.pdf"

                    report.report_pdf.save(
                        pdf_name,
                        ContentFile(
                            pdf_response.content
                        ),
                        save=False
                    )

            # =========================================
            # SUCCESS REPORT
            # =========================================

            report.status = "SUCCESS"

            report.response_message = str(
                response_data
            )

            report.save()

            # =========================================
            # CUSTOMER WALLET DEDUCTION
            # =========================================

            opening_balance = (
                customer_wallet.balance
            )

            closing_balance = (
                opening_balance - customer_price
            )

            customer_wallet.balance = (
                closing_balance
            )

            customer_wallet.save()

            # =========================================
            # WALLET TRANSACTION
            # =========================================

            wallet_txn = WalletTransaction.objects.create(

                user=customer,

                reference_id=str(
                    uuid.uuid4()
                ),

                amount=customer_price,

                txn_type="debit",

                service=report_type,

                narration=(
                    f"{report_type} report generated"
                )
            )

            # =========================================
            # WALLET LEDGER
            # =========================================

            WalletLedger.objects.create(

                wallet=customer_wallet,

                transaction=wallet_txn,

                opening_balance=opening_balance,

                amount=customer_price,

                closing_balance=closing_balance,

                entry_type="debit"
            )

            # =========================================
            # AGENT PLAN DEDUCT
            # =========================================

            agent_plan.remaining_balance -= (
                agent_cost_price
            )

            agent_plan.save()

            # =========================================
            # PROFIT
            # =========================================

            profit = (
                customer_price
                - agent_cost_price
            )

            # =========================================
            # SAVE USAGE
            # =========================================

            PlanUsage.objects.create(

                agent=agent,

                customer=customer,

                report=report,

                service=report_type,

                status="SUCCESS",

                cost_price=agent_cost_price,

                price=customer_price,

                profit=profit,

                reference_id=str(report.id)

            )

            # =========================================
            # RESPONSE
            # =========================================

            return Response(
                {
                    "status": True,

                    "message":
                        "Report Generated Successfully",

                    "report_id":
                        str(report.id),

                    "pdf": (
                        report.report_pdf.url
                        if report.report_pdf
                        else None
                    ),

                    "data": response_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:

            if report:

                report.status = "FAILED"

                report.response_message = str(e)

                report.save()

            return Response(
                {
                    "status": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
