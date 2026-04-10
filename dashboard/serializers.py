from rest_framework import serializers
from cibil.models import PlanUsage


class AgentCustomerTransactionSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(source="customer.username", read_only=True)
    customer_id = serializers.IntegerField(source="customer.id", read_only=True)

    report_type = serializers.CharField(source="report.report_type", read_only=True)

    # 🔥 FIX
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        if obj.report and obj.report.status:
            return obj.report.status
        return "SUCCESS"

    created_at = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        if obj.report and obj.report.created_at:
            return obj.report.created_at
        return obj.created_at

    class Meta:
        model = PlanUsage
        fields = [
            "id",
            "customer_id",
            "customer_name",
            "service",
            "price",
            "cost_price",
            "profit",
            "reference_id",
            "report_type",
            "status",
            "created_at",
        ]