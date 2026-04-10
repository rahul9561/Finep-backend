from .models import Wallet, WalletTransaction, WalletLedger
from rest_framework import serializers

class WalletTransactionSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "username",
            "amount",
            "txn_type",
            "service",
            "narration",
            "reference_id",
            "created_at",
        ]