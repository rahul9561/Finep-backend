from rest_framework import serializers
import re
from .models import CibilReport


class CibilReportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    mobile = serializers.CharField(max_length=10)
    pan = serializers.CharField(max_length=10)

    gender = serializers.ChoiceField(choices=["male", "female"])
    report_type = serializers.ChoiceField(
        choices=["cibil", "experian", "equifax", "crif"]
    )

    # 🔹 extra fields for equifax
    dob = serializers.DateField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    pincode = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        return value.strip()

    def validate_mobile(self, value):
        if not re.match(r"^[6-9]\d{9}$", value):
            raise serializers.ValidationError(
                "Enter valid 10-digit Indian mobile number"
            )
        return value

    def validate_pan(self, value):
        value = value.upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", value):
            raise serializers.ValidationError(
                "Invalid PAN format (e.g., ABCDE1234F)"
            )
        return value

    def validate(self, data):
        # 🔹 equifax ke liye required fields check
        if data.get("report_type") == "equifax":
            required = ["dob" , "address", "state", "pincode"]
            for field in required:
                if not data.get(field):
                    raise serializers.ValidationError(
                        {field: f"{field} is required for Equifax report"}
                    )
        return data

    def validate_report_type(self, value):
        return value.lower()


from rest_framework import serializers
from .models import RechargePlan

class RechargePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargePlan
        fields = "__all__"


# cibil/serializers.py
from rest_framework import serializers
from .models import AgentPlan

class PlanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargePlan
        fields = [
            "id",
            "title",
            "plan_type",

            # 🔥 ALL PRICES
            "aadhaar_price",
            "pan_verify_price",
            "gst_verify_price",
            "bank_verify_price",

            "cibil_price",
            "crif_price",
            "equifax_price",
            "experian_price",
            "prefill_price",
        ]


class AgentPlanSerializer(serializers.ModelSerializer):

    plan_title = serializers.CharField(source="plan.title", read_only=True)
    plan = PlanDetailSerializer(read_only=True)  # ✅ nested

    class Meta:
        model = AgentPlan
        fields = [
            "id",
            "plan_title",
            "plan",
            "remaining_balance",
            "is_active",
            "created_at",
        ]



# cibil/serializers.py

# serializers.py
class AdminCibilReportSerializer(serializers.ModelSerializer):

    agent_name = serializers.CharField(source="agent.username")
    agent_email = serializers.CharField(source="agent.email")

    class Meta:
        model = CibilReport
        fields = [
            "id",
            "agent_name",
            "agent_email",
            "name",
            "mobile",
            "pan",
            "report_type",
            "status",
            "created_at",
            "report_pdf"
        ]
        
        
# cibil/serializers.py

class PlanPriceUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = RechargePlan
        fields = [
            "prefill_price",
            "cibil_price",
            "crif_price",
            "equifax_price",
            "experian_price",
            "cibil_commercial"
            
            # 🔥 ADD THIS
            "pan_verify_price",
            "gst_verify_price",
            "bank_verify_price"
        ]
        
        
# serializers.py

