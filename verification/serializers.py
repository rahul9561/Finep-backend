from rest_framework import serializers
from .models import *


class BankReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankVerificationReport
        fields = "__all__"


class PanReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanVerificationReport
        fields = "__all__"


class AadhaarReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AadhaarValidationReport
        fields = "__all__"


class GSTReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTReport
        fields = "__all__"


class MSMESerializer(serializers.ModelSerializer):
    class Meta:
        model = MSMEReport
        fields = "__all__"


class RCSerializer(serializers.ModelSerializer):
    class Meta:
        model = RCReport
        fields = "__all__"


class ElectricitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityReport
        fields = "__all__"
        
        
        
# serializers.py

class APIPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIPricing
        fields = "__all__"
        
        
from rest_framework import serializers
from cibil.models import PlanUsage


from rest_framework import serializers
from cibil.models import PlanUsage


class CustomerReportHistorySerializer(serializers.ModelSerializer):

    report_id = serializers.UUIDField(source="report.id", read_only=True)
    report_type = serializers.CharField(source="report.report_type", read_only=True)
    status = serializers.CharField(read_only=True)

    # 🔥 FIX HERE
    created_at = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        if obj.report and obj.report.created_at:
            return obj.report.created_at
        return obj.created_at   # ✅ fallback

    class Meta:
        model = PlanUsage
        fields = [
            "id",
            "service",
            "price",
            "cost_price",
            "profit",
            "reference_id",
            "report_id",
            "report_type",
            "status",
            "created_at",
        ]