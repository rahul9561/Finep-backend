from django.contrib import admin
from .models import Wallet, WalletTransaction, WalletLedger


# ---------------- WALLET ----------------

from django.contrib import admin
from decimal import Decimal

from .models import Wallet, WalletTransaction, WalletLedger


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "balance",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "updated_at",
    )

    def save_model(self, request, obj, form, change):

        if not change:
            super().save_model(request, obj, form, change)
            return

        old_wallet = Wallet.objects.get(pk=obj.pk)

        old_balance = old_wallet.balance
        new_balance = obj.balance

        diff = Decimal(new_balance) - Decimal(old_balance)

        super().save_model(request, obj, form, change)

        if diff == 0:
            return

        # CREDIT

        if diff > 0:

            txn = WalletTransaction.objects.create(
                user=obj.user,
                reference_id=f"ADMIN-CREDIT-{obj.id}",
                amount=diff,
                txn_type="credit",
                service="ADMIN",
                narration="Admin balance added",
            )

            WalletLedger.objects.create(
                wallet=obj,
                transaction=txn,
                opening_balance=old_balance,
                amount=diff,
                closing_balance=new_balance,
                entry_type="credit",
            )

        # DEBIT

        else:

            diff = abs(diff)

            txn = WalletTransaction.objects.create(
                user=obj.user,
                reference_id=f"ADMIN-DEBIT-{obj.id}",
                amount=diff,
                txn_type="debit",
                service="ADMIN",
                narration="Admin balance deducted",
            )

            WalletLedger.objects.create(
                wallet=obj,
                transaction=txn,
                opening_balance=old_balance,
                amount=diff,
                closing_balance=new_balance,
                entry_type="debit",
            )


# ---------------- TRANSACTION ----------------

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "reference_id",
        "user",
        "amount",
        "txn_type",
        "service",
        "created_at",
    )

    list_filter = (
        "txn_type",
        "service",
        "created_at",
    )

    search_fields = (
        "reference_id",
        "user__username",
        "service",
    )

    readonly_fields = (
        "reference_id",
        "created_at",
    )

    ordering = ("-created_at",)


# ---------------- LEDGER ----------------

@admin.register(WalletLedger)
class WalletLedgerAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "wallet",
        "transaction",
        "opening_balance",
        "amount",
        "closing_balance",
        "entry_type",
        "created_at",
    )

    list_filter = (
        "entry_type",
        "created_at",
    )

    search_fields = (
        "wallet__user__username",
        "transaction__reference_id",
    )

    readonly_fields = (
        "opening_balance",
        "closing_balance",
        "created_at",
    )

    ordering = ("-created_at",)