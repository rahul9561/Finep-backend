from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# Fix: gst_service, msme_service, rc_service, electricity_service were missing
from verification.services.services import (
    bank_verification_service,
    pan_verification_service,
    aadhaar_validation_service,
    gst_service,
    msme_service,
    rc_service,
    electricity_service,
)


class BankVerificationView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        id_number = request.data.get("id_number")
        ifsc = request.data.get("ifsc")

        if not id_number or not ifsc:
            return Response(
                {"status": False, "message": "id_number and ifsc are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = bank_verification_service(request.user, id_number, ifsc)

        # ✅ correct check
        if not result.get("status"):
            return Response(
                {
                    "status": False,
                    "message": result.get("message", "Verification failed"),
                    "data": result.get("provider_response"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class PanVerifyView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_number = request.data.get("id_number")

        if not id_number:
            return Response(
                {"status": False, "message": "id_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = pan_verification_service(
            request.user,
            id_number,
            request.data.get("full_name"),
            request.data.get("dob"),
        )
        return Response(result, status=status.HTTP_200_OK if result["status"] else status.HTTP_400_BAD_REQUEST)


class AadhaarValidationView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_number = request.data.get("id_number")

        if not id_number:
            return Response(
                {"status": False, "message": "id_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = aadhaar_validation_service(request.user, id_number)
        return Response(result, status=status.HTTP_200_OK if result["status"] else status.HTTP_400_BAD_REQUEST)


class GSTView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_number = request.data.get("id_number")

        if not id_number:
            return Response(
                {"status": False, "message": "id_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = gst_service(request.user, id_number)
        return Response(result, status=status.HTTP_200_OK if result["status"] else status.HTTP_400_BAD_REQUEST)


class MSMEView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        pan = request.data.get("pan")

        if not pan:
            return Response(
                {"status": False, "message": "pan is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = msme_service(request.user, pan)
        return Response(result, status=status.HTTP_200_OK if result["status"] else status.HTTP_400_BAD_REQUEST)


class RCView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        rc_number = request.data.get("rc_number")

        if not rc_number:
            return Response(
                {"status": False, "message": "rc_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = rc_service(request.user, rc_number)
        return Response(result, status=status.HTTP_200_OK if result["status"] else status.HTTP_400_BAD_REQUEST)


class ElectricityView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_number = request.data.get("id_number")
        operator_code = request.data.get("operator_code")

        if not id_number or not operator_code:
            return Response(
                {"status": False, "message": "id_number and operator_code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = electricity_service(request.user, id_number, operator_code)
        return Response(result, status=status.HTTP_200_OK if result["status"] else status.HTTP_400_BAD_REQUEST)
    
    
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from .models import *
from .serializers import *


class AdminDashboardView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):

        data = {

            "counts": {

                "bank": BankVerificationReport.objects.count(),
                "pan": PanVerificationReport.objects.count(),
                "aadhaar": AadhaarValidationReport.objects.count(),
                "gst": GSTReport.objects.count(),
                "msme": MSMEReport.objects.count(),
                "rc": RCReport.objects.count(),
                "electricity": ElectricityReport.objects.count(),

            },

            "latest": {

                "bank": BankReportSerializer(
                    BankVerificationReport.objects.order_by("-id")[:5],
                    many=True
                ).data,

                "pan": PanReportSerializer(
                    PanVerificationReport.objects.order_by("-id")[:5],
                    many=True
                ).data,

                "aadhaar": AadhaarReportSerializer(
                    AadhaarValidationReport.objects.order_by("-id")[:5],
                    many=True
                ).data,

                "gst": GSTReportSerializer(
                    GSTReport.objects.order_by("-id")[:5],
                    many=True
                ).data,

                "msme": MSMESerializer(
                    MSMEReport.objects.order_by("-id")[:5],
                    many=True
                ).data,

                "rc": RCSerializer(
                    RCReport.objects.order_by("-id")[:5],
                    many=True
                ).data,

                "electricity": ElectricitySerializer(
                    ElectricityReport.objects.order_by("-id")[:5],
                    many=True
                ).data,
            }

        }

        return Response(data)
    
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from django.contrib.auth import get_user_model

from .models import *

User = get_user_model()


class AdminActivityView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):

        data = []

        # -------- BANK -------- #

        for i in BankVerificationReport.objects.all():

            data.append({

                "type": "BANK",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.id_number,
                "status": i.status,   # ✅ added
                "date": i.created_at,

            })

        # -------- PAN -------- #

        for i in PanVerificationReport.objects.all():

            data.append({

                "type": "PAN",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.pan_number,
                "status": i.status,
                "date": i.created_at,

            })

        # -------- AADHAAR -------- #

        for i in AadhaarValidationReport.objects.all():

            data.append({

                "type": "AADHAAR",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.aadhaar_number,
                "status": i.status,
                "date": i.created_at,

            })

        # -------- GST -------- #

        for i in GSTReport.objects.all():

            data.append({

                "type": "GST",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.gst_number,
                "status": i.status,
                "date": i.created_at,

            })

        # -------- MSME -------- #

        for i in MSMEReport.objects.all():

            data.append({

                "type": "MSME",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.pan,
                "status": i.status,
                "date": i.created_at,

            })

        # -------- RC -------- #

        for i in RCReport.objects.all():

            data.append({

                "type": "RC",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.rc_number,
                "status": i.status,
                "date": i.created_at,

            })

        # -------- ELECTRICITY -------- #

        for i in ElectricityReport.objects.all():

            data.append({

                "type": "ELECTRICITY",
                "username": i.user.username,
                "mobile": i.user.mobile,
                "number": i.id_number,
                "status": i.status,
                "date": i.created_at,

            })

        # latest first
        data = sorted(data, key=lambda x: x["date"], reverse=True)

        return Response(data)
    
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import APIPricing
from .serializers import APIPricingSerializer



class SetAPIPricingView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user

        if user.role != "agent":
            return Response(
                {"status": False, "message": "Only agent can set pricing"},
                status=status.HTTP_403_FORBIDDEN
            )

        service = request.data.get("service")
        price = request.data.get("price")
        customer_id = request.data.get("customer_id")   # ✅ NEW

        # ✅ validation
        if not service or not price:
            return Response(
                {"status": False, "message": "service and price are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            price = float(price)
        except:
            return Response(
                {"status": False, "message": "Invalid price"},
                status=status.HTTP_400_BAD_REQUEST
            )

        customer = None

        # ✅ handle customer-specific pricing
        if customer_id:
            try:
                customer = User.objects.get(
                    id=customer_id,
                    created_by=user   # 🔒 only own customers
                )
            except User.DoesNotExist:
                return Response(
                    {"status": False, "message": "Invalid customer"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        obj, created = APIPricing.objects.update_or_create(
            agent=user,
            customer=customer,   # 🔥 KEY CHANGE
            service=service,
            defaults={"price": price}
        )

        return Response({
            "status": True,
            "message": "Price set successfully",
            "data": APIPricingSerializer(obj).data
        })


class GetMyPricingView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.role != "agent":
            return Response(
                {"status": False, "message": "Only agent allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        prices = APIPricing.objects.filter(agent=request.user)

        data = []
        for p in prices:
            data.append({
                "service": p.service,
                "price": p.price,
                "customer": p.customer.username if p.customer else "ALL"
            })

        return Response({
            "status": True,
            "count": len(data),
            "data": data
        })
        
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# from wallet.models import Transaction
# from wallet.serializers import TransactionSerializer
from wallet.models import WalletTransaction
from wallet.serializers import WalletTransactionSerializer
from accounts.models import User


class AgentCustomerTransactionsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if user.role != "agent":
            return Response(
                {"status": False, "message": "Only agent allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        customers = User.objects.filter(created_by=user)

        transactions = WalletTransaction.objects.filter(
            user__in=customers
        ).order_by("-id")

        return Response({
            "status": True,
            "count": transactions.count(),
            "data": WalletTransactionSerializer(transactions, many=True).data
        })
        
from verification.models import (
    BankVerificationReport,
    PanVerificationReport,
    AadhaarValidationReport,
    GSTReport,
    MSMEReport,
    RCReport,
    ElectricityReport,
)


class AgentCustomerReportsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if user.role != "agent":
            return Response(
                {"status": False, "message": "Only agent allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        customers = User.objects.filter(created_by=user)

        data = []

        # 🔥 BANK
        for i in BankVerificationReport.objects.filter(user__in=customers):
            data.append({
                "type": "BANK",
                "customer": i.user.username,
                "number": i.id_number,
                "status": i.status,
                "date": i.created_at
            })

        # 🔥 PAN
        for i in PanVerificationReport.objects.filter(user__in=customers):
            data.append({
                "type": "PAN",
                "customer": i.user.username,
                "number": i.pan_number,
                "status": i.status,
                "date": i.created_at
            })

        # 🔥 AADHAAR
        for i in AadhaarValidationReport.objects.filter(user__in=customers):
            data.append({
                "type": "AADHAAR",
                "customer": i.user.username,
                "number": i.aadhaar_number,
                "status": i.status,
                "date": i.created_at
            })

        # 🔥 GST
        for i in GSTReport.objects.filter(user__in=customers):
            data.append({
                "type": "GST",
                "customer": i.user.username,
                "number": i.gst_number,
                "status": i.status,
                "date": i.created_at
            })

        # 🔥 MSME
        for i in MSMEReport.objects.filter(user__in=customers):
            data.append({
                "type": "MSME",
                "customer": i.user.username,
                "number": i.pan,
                "status": i.status,
                "date": i.created_at
            })

        # 🔥 RC
        for i in RCReport.objects.filter(user__in=customers):
            data.append({
                "type": "RC",
                "customer": i.user.username,
                "number": i.rc_number,
                "status": i.status,
                "date": i.created_at
            })

        # 🔥 ELECTRICITY
        for i in ElectricityReport.objects.filter(user__in=customers):
            data.append({
                "type": "ELECTRICITY",
                "customer": i.user.username,
                "number": i.id_number,
                "status": i.status,
                "date": i.created_at
            })

        # 👉 latest first
        data = sorted(data, key=lambda x: x["date"], reverse=True)

        return Response({
            "status": True,
            "count": len(data),
            "data": data
        })
        
        
        
        
        
        
        
        
        
        
# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cibil.models import PlanUsage
from .serializers import CustomerReportHistorySerializer


class CustomerReportHistoryView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        # ✅ Safe role check
        if user.role != user.Role.CUSTOMER:
            return Response({
                "status": False,
                "message": "Only customer allowed"
            }, status=403)

        # 🔥 Query (optimized)
        reports = PlanUsage.objects.filter(
            customer=user
        ).order_by("-created_at")

        # 🔥 Pagination (simple)
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        start = (page - 1) * limit
        end = start + limit

        total = reports.count()
        reports = reports[start:end]

        serializer = CustomerReportHistorySerializer(reports, many=True)

        return Response({
            "status": True,
            "count": total,
            "page": page,
            "limit": limit,
            "data": serializer.data
        })