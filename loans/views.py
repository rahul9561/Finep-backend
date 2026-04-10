# new code
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from loans.svatantr.client import SvatantrClient
from loans.svatantr.service import LoanService
from agent.models import Agent
from customer.models import Customer
from loans.serializers import LoanLeadCreateSerializer,LoanLeadListSerializer
from loans.models import LoanLead
from loans.svatantr.service import SvatantrSyncService
from loans.models import LoanLead, SyncLog
from datetime import datetime, timedelta

class CategoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        pincode = request.GET.get("pincode")

        if not pincode:
            return Response(
                {"error": "pincode required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            client = SvatantrClient()

            data = client.get_categories(
                pincode=pincode
            )

            return Response({
                "success": True,
                "data": data
            })

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
            
class BanksAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        category_id = request.GET.get("category_id")
        pincode = request.GET.get("pincode")

        if not category_id or not pincode:
            return Response(
                {"error": "category_id & pincode required"},
                status=400,
            )

        try:

            client = SvatantrClient()

            data = client.get_banks(
                category_id=category_id,
                pincode=pincode,
            )

            # return Response({
            #     "success": True,
            #     "data": data
            # })
            return Response(data)

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=500,
            )
  
  
  
class JourneyAPIView(APIView):

    def get(self, request):

        category_id = request.GET.get("categoryId")

        client = SvatantrClient()

        data = client.get_journey(category_id)

        return Response(data)          
            
            
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class CreateLoanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("REQUEST DATA:", request.data)

        service = LoanService()

        try:

            lead = service.create_lead(
                user=request.user,
                data=request.data,
            )

            return Response({
                "success": lead.status != "FAILED",   # ✅ better
                "lead_id": lead.id,
                "status": lead.status,
                "redirect_url": lead.redirect_url,
                "provider_response": lead.provider_response,  # ✅ add this
                # "message": lead.status_message,
                "message": lead.status_message or lead.provider_response,
            })

        except Exception as e:

            return Response({
                "success": False,
                "message": str(e),
            }, status=400)
            

# views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import LoanLead
from .serializers import LoanLeadListSerializer


# class LoanListAPIView(APIView):

#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         qs = LoanLead.objects.all().order_by("-id")

#         serializer = LoanLeadListSerializer(
#             qs,
#             many=True
#         )

#         return Response({
#             "success": True,
#             "data": serializer.data
#         })
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.core.paginator import Paginator
from django.db.models import Q

from .models import LoanLead
from .serializers import LoanLeadListSerializer


class LoanListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        qs = LoanLead.objects.all().order_by("-id")

        # -----------------------
        # Only own leads
        # -----------------------

        if not request.user.is_staff:
            qs = qs.filter(created_by=request.user)

        # -----------------------
        # FILTER status
        # ?status=APPROVED
        # -----------------------

        status_param = request.GET.get("status")

        if status_param:
            qs = qs.filter(status=status_param)

        # -----------------------
        # FILTER bank
        # ?bank=HDFC
        # -----------------------

        bank = request.GET.get("bank")

        if bank:
            qs = qs.filter(bank_name__icontains=bank)

        # -----------------------
        # SEARCH
        # ?search=rahul
        # -----------------------

        search = request.GET.get("search")

        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(mobile__icontains=search)
                | Q(application_no__icontains=search)
                | Q(provider_lead_id__icontains=search)
            )

        # -----------------------
        # DATE FILTER
        # ?from_date=2026-03-01
        # ?to_date=2026-03-15
        # -----------------------

        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")

        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)

        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        # -----------------------
        # PAGINATION
        # ?page=1&page_size=10
        # -----------------------

        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        paginator = Paginator(qs, page_size)

        page_obj = paginator.get_page(page)

        serializer = LoanLeadListSerializer(
            page_obj,
            many=True
        )

        return Response({
            "success": True,
            "page": page,
            "total_pages": paginator.num_pages,
            "total_records": paginator.count,
            "data": serializer.data,
        })

        
class SalaryCheckAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        salary = request.GET.get("salary")

        if not salary:
            return Response(
                {"error": "salary required"},
                status=400,
            )

        salary = int(salary)

        try:

            client = SvatantrClient()

            settings_data = client.get_master_settings()

            rules = settings_data["data"]

            min_salary = None

            for r in rules:

                if r["name"] == "SALARY_AMOUNT":
                    # convert paisa → rupees
                    min_salary = r["value"] / 1000
                    # min_salary = r["value"]

            if min_salary and salary < min_salary:

                return Response(
                    {
                        "allowed": False,
                        "message": f"Minimum salary {min_salary}"
                    }
                )

            return Response(
                {
                    "allowed": True
                }
            )

        except Exception as e:

            return Response(
                {"error": str(e)},
                status=500,
            )
            
            
# loans/views.py

from rest_framework.views import APIView
from rest_framework.response import Response

        
from loans.svatantr.service import SvatantrSyncService

class SvatantrSyncAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        result = SvatantrSyncService().sync()

        return Response({
            "success": True,
            "data": result
        })
        
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from loans.models import LoanLead

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from loans.models import LoanLead


class MISAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        status_filter = request.GET.get("status")
        agent_filter = request.GET.get("agent")

        skip = (page - 1) * page_size
        limit = page_size

        # =========================
        # GET MIS FROM SVATANTR
        # =========================

        from datetime import datetime, timedelta

        start = (
            datetime.today() - timedelta(days=30)
        ).strftime("%Y-%m-%d")

        end = datetime.today().strftime("%Y-%m-%d")

        mis_data = SvatantrSyncService().get_mis_data(
            skip=skip,
            limit=limit,
            status=status_filter,
            start=start,
            end=end,
        )

        data_block = mis_data.get("data", {})
        mis_result = data_block.get("result", [])

        # =========================
        # DB QUERY
        # =========================

        qs = LoanLead.objects.all()

        if not request.user.is_staff:
            qs = qs.filter(created_by=request.user)

        if status_filter:
            qs = qs.filter(status=status_filter)

        if agent_filter:
            qs = qs.filter(created_by_id=agent_filter)

        # map provider_lead_id → lead

        lead_map = {
            str(lead.provider_lead_id): lead
            for lead in qs.select_related("created_by")
        }

        # =========================
        # MERGE DATA
        # =========================

        final_list = []
        seen = set()

        for item in mis_result:

            provider_id = str(item.get("_id"))

            if provider_id in seen:
                continue

            seen.add(provider_id)

            lead = lead_map.get(provider_id)

            if lead:
                item["agent_name"] = (
                    lead.created_by.name
                    if lead.created_by else None
                )

                item["local_status"] = lead.status

            else:
                item["agent_name"] = None
                item["local_status"] = None

            final_list.append(item)

        # =========================
        # TOTAL RECORDS
        # =========================

        total_records = data_block.get("total")

        if not total_records:
            total_records = len(mis_result)

        # =========================
        # STATS FROM DB
        # =========================

        stats = {
            "total": qs.count(),
            "approved": qs.filter(status="APPROVED").count(),
            "rejected": qs.filter(status="REJECTED").count(),
            "processing": qs.filter(status="PROCESSING").count(),
            "created": qs.filter(status="CREATED").count(),
            "disbursed": qs.filter(status="DISBURSED").count(),
        }

        # =========================
        # RESPONSE
        # =========================

        return Response({

            "success": True,

            "stats": stats,

            "page": page,
            "page_size": page_size,

            "total_records": total_records,

            "mis": final_list,

        })
        
        
        
        
        
        
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.core.paginator import Paginator
from django.db.models import Q

from loans.models import LoanLead
from loans.serializers import LoanLeadListSerializer


class AdminLoanListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        qs = LoanLead.objects.all().order_by("-id")

        # =========================
        # ONLY OWN LEADS (AGENT)
        # =========================

        if not request.user.is_staff:
            qs = qs.filter(created_by=request.user)

        # =========================
        # ADMIN FILTER BY AGENT
        # ?agent=5
        # =========================

        agent = request.GET.get("agent")

        if agent:
            qs = qs.filter(created_by_id=agent)

        # =========================
        # STATUS FILTER
        # =========================

        status_param = request.GET.get("status")

        if status_param:
            qs = qs.filter(status=status_param)

        # =========================
        # BANK FILTER
        # =========================

        bank = request.GET.get("bank")

        if bank:
            qs = qs.filter(bank_name__icontains=bank)

        # =========================
        # SEARCH
        # =========================

        search = request.GET.get("search")

        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(mobile__icontains=search)
                | Q(application_no__icontains=search)
                | Q(provider_lead_id__icontains=search)
            )

        # =========================
        # DATE FILTER
        # =========================

        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")

        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)

        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        # =========================
        # PAGINATION
        # =========================

        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        paginator = Paginator(qs, page_size)
        page_obj = paginator.get_page(page)

        serializer = LoanLeadListSerializer(
            page_obj,
            many=True
        )

        # =========================
        # STATS (ADMIN + AGENT)
        # =========================

        stats_qs = LoanLead.objects.all()

        if not request.user.is_staff:
            stats_qs = stats_qs.filter(created_by=request.user)

        if agent:
            stats_qs = stats_qs.filter(created_by_id=agent)

        stats = {
            "total": stats_qs.count(),
            "approved": stats_qs.filter(status="APPROVED").count(),
            "rejected": stats_qs.filter(status="REJECTED").count(),
            "processing": stats_qs.filter(status="PROCESSING").count(),
            "created": stats_qs.filter(status="CREATED").count(),
            "disbursed": stats_qs.filter(status="DISBURSED").count(),
        }

        # =========================
        # RESPONSE
        # =========================

        return Response({
            "success": True,
            "page": page,
            "total_pages": paginator.num_pages,
            "total_records": paginator.count,
            "stats": stats,
            "data": serializer.data,
        })
        