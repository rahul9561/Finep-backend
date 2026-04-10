from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from services.credit_partner_balance import PaySprintService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def main_balance_view(request):
    result = PaySprintService.get_main_balance()
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cash_balance_view(request):
    result = PaySprintService.get_cash_balance()
    return Response(result)