import uuid
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Wallet, WalletTransaction, WalletLedger


# ============================
# CREDIT
# ============================

def wallet_credit(user, amount, service="", note=""):

    try:
        amount = Decimal(amount)
    except InvalidOperation:
        raise Exception("Invalid amount")

    if amount <= 0:
        raise Exception("Amount must be greater than 0")

    with transaction.atomic():

        wallet, _ = Wallet.objects.select_for_update().get_or_create(
            user=user
        )

        opening = wallet.balance

        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=["balance"])

        ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        txn = WalletTransaction.objects.create(
            user=user,
            reference_id=ref,
            amount=amount,
            txn_type="credit",
            service=service,
            narration=note,
        )

        WalletLedger.objects.create(
            wallet=wallet,
            transaction=txn,
            opening_balance=opening,
            amount=amount,
            closing_balance=wallet.balance,
            entry_type="credit",
        )

        return txn


# ============================
# DEBIT
# ============================

def wallet_debit(user, amount, service="", note=""):

    try:
        amount = Decimal(amount)
    except InvalidOperation:
        raise Exception("Invalid amount")

    if amount <= 0:
        raise Exception("Amount must be greater than 0")

    with transaction.atomic():

        wallet = Wallet.objects.select_for_update().filter(
            user=user
        ).first()

        if not wallet:
            raise Exception("Wallet not found")

        if wallet.balance < amount:
            raise Exception("Insufficient wallet balance")

        opening = wallet.balance

        wallet.balance = wallet.balance - amount
        wallet.save(update_fields=["balance"])

        ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        txn = WalletTransaction.objects.create(
            user=user,
            reference_id=ref,
            amount=amount,
            txn_type="debit",
            service=service,
            narration=note,
        )

        WalletLedger.objects.create(
            wallet=wallet,
            transaction=txn,
            opening_balance=opening,
            amount=amount,
            closing_balance=wallet.balance,
            entry_type="debit",
        )

        return txn