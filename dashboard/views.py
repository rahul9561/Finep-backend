from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from wallet.models import Wallet
from cibil.models import AgentPlan
from django.db.models import Sum


class DashboardSummaryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        wallet = Wallet.objects.filter(user=request.user).first()

        plans = AgentPlan.objects.filter(
            agent=request.user,
            is_active=True
        )

        total_balance = plans.aggregate(
            total=Sum("remaining_balance")
        )["total"] or 0

        return Response({
            "wallet": {
                "main": wallet.balance if wallet else 0,
                "aeps": 0,
                "cibil": total_balance
            }
        })


# dashboard/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from cibil.models import PlanUsage
from wallet.models import Wallet


class AgentDashboardAPIView(APIView):

    def get(self, request):
        agent = request.user

        # 🔥 total earnings
        total_profit = PlanUsage.objects.filter(
            agent=agent
        ).aggregate(total=Sum("profit"))["total"] or 0

        # 🔥 total usage
        total_usage = PlanUsage.objects.filter(
            agent=agent
        ).count()

        # 🔥 wallet balance
        wallet = Wallet.objects.filter(user=agent).first()
        balance = wallet.balance if wallet else 0

        # 🔥 service-wise earnings
        service_data = PlanUsage.objects.filter(
            agent=agent
        ).values("service").annotate(
            total_profit=Sum("profit"),
            total_hits=Count("id")
        )

        return Response({
            "total_profit": total_profit,
            "total_usage": total_usage,
            "wallet_balance": balance,
            "service_data": service_data
        })
        
# dashboard/views.py

from wallet.models import WalletTransaction

class RecentTransactionsAPIView(APIView):

    def get(self, request):
        agent = request.user

        txns = WalletTransaction.objects.filter(
            user=agent
        ).order_by("-created_at")[:10]

        data = [
            {
                "amount": t.amount,
                "type": t.txn_type,
                "service": t.service,
                "date": t.created_at
            }
            for t in txns
        ]

        return Response(data)
    
    
    
    
# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, Count

from wallet.models import Wallet
from cibil.models import AgentPlan, PlanUsage
from verification.models import *



class CustomerDashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        # ✅ Proper role check
        if user.role != user.Role.CUSTOMER:
            return Response({
                "status": False,
                "message": "Only customer allowed"
            }, status=403)

        # 🔥 Wallet Balance (safe)
        wallet_balance = getattr(getattr(user, "wallet", None), "balance", 0)

        # 🔥 Agent Plan Balance
        agent = user.created_by

        plan_balance = 0
        if agent:
            plan_balance = AgentPlan.objects.filter(
                agent=agent,
                is_active=True
            ).aggregate(total=Sum("remaining_balance"))["total"] or 0

        # 🔥 Only customer usages (extra safety)
        usages = PlanUsage.objects.filter(
            customer=user,
            customer__role=user.Role.CUSTOMER   # ✅ ADD THIS FILTER
        )

        total_reports = usages.count()

        total_spend = usages.aggregate(
            total=Sum("price")
        )["total"] or 0

        # 🔥 Service-wise count
        service_stats = usages.values("service").annotate(
            count=Count("id")
        )

        # 🔥 Recent Activity
        recent = usages.order_by("-created_at")[:5]
        

        recent_data = [
            {
                "service": i.service,
                "price": i.price,
                "status": i.status,
                "date": i.created_at,
            }
            for i in recent
            
        ]
        

        return Response({
            "status": True,
            "data": {
                "wallet_balance": wallet_balance,
                "total_reports": total_reports,
                "total_spend": total_spend,
                "service_stats": service_stats,
                "recent_activity": recent_data,
            }
        })
        
        
        
# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cibil.models import PlanUsage
from .serializers import AgentCustomerTransactionSerializer


class AgentCustomerTransactionsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        # 🔒 only agent allowed
        if user.role != "agent":
            return Response({
                "status": False,
                "message": "Only agent allowed"
            }, status=403)

        # 🔥 only agent's customers
        transactions = PlanUsage.objects.filter(
            agent=user,
            customer__created_by=user   # ✅ IMPORTANT FIX
        ).select_related("customer", "report").order_by("-created_at")

        serializer = AgentCustomerTransactionSerializer(transactions, many=True)

        return Response({
            "status": True,
            "count": transactions.count(),
            "data": serializer.data
        })