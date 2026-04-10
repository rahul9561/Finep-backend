import uuid
import json
import requests
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import PaymentOrder
from wallet.services import wallet_credit
from wallet.models import WalletTransaction


# ============================
# CREATE ORDER
# ============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    user = request.user
    print("User:", user)  # Debugging statement

    amount = request.data.get("amount")

    # 🔥 VALIDATION
    try:
        amount = Decimal(amount)
        if amount <= 0:
            return Response({"message": "Invalid amount"}, status=400)
    except:
        return Response({"message": "Invalid amount"}, status=400)

    order_id = f"CUST_{user.id}_{uuid.uuid4().hex[:8]}"

    # 🔥 SAVE ORDER
    PaymentOrder.objects.create(
        user=user,
        order_id=order_id,
        amount=amount
    )

    url = f"{settings.CASHFREE_BASE_URL}/pg/orders"

    payload = {
        "order_id": order_id,
        "order_amount": float(amount),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user.id),
            "customer_email": user.email,
            "customer_phone": user.mobile,
        },
        "order_meta": {
        "return_url": "http://localhost:5173"
    }
    }

    headers = {
        "x-client-id": settings.CASHFREE_CLIENT_ID,
        "x-client-secret": settings.CASHFREE_CLIENT_SECRET,
        "x-api-version": "2025-01-01",   # 🔥 IMPORTANT
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)
    print("==== CASHFREE DEBUG ====")
    print("STATUS CODE:", res.status_code)
    print("RESPONSE:", res.text)
    print("PAYLOAD:", payload)
    print("========================")

    if res.status_code != 200:
        return Response({
            "message": "Order creation failed",
            "error": res.text
        }, status=400)

    return Response(res.json())


# ============================
# WEBHOOK
# ============================

@csrf_exempt
def cashfree_webhook(request):
    if request.method != "POST":
        return HttpResponse("Invalid method")

    try:
        data = json.loads(request.body)
    except Exception as e:
        print("❌ JSON ERROR:", e)
        return HttpResponse("Invalid JSON", status=400)

    print("🔥 WEBHOOK HIT:", data)

    event_type = data.get("type")

    # ✅ TEST WEBHOOK
    if event_type == "WEBHOOK" and "test_object" in data.get("data", {}):
        return HttpResponse("OK")

    # 🔥 REAL DATA
    data_obj = data.get("data", {})

    order_data = data_obj.get("order", {})
    payment_data = data_obj.get("payment", {})

    order_id = order_data.get("order_id")
    status = payment_data.get("payment_status")

    print("👉 ORDER ID:", order_id)
    print("👉 STATUS:", status)

    if not order_id:
        return HttpResponse("No order id")

    if status != "SUCCESS":
        return HttpResponse("Not success")

    order = PaymentOrder.objects.filter(order_id=order_id).first()

    if not order:
        return HttpResponse("Order not found")

    if WalletTransaction.objects.filter(reference_id=order_id).exists():
        return HttpResponse("Already credited")

    if order.status == "PAID":
        return HttpResponse("Already processed")

    wallet_credit(
        user=order.user,
        amount=order.amount,
        service="wallet_recharge",
        note="Cashfree payment"
    )

    order.status = "PAID"
    order.save()

    print("✅ WALLET CREDITED SUCCESS")

    return HttpResponse("OK")