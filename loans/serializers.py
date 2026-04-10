
        
        
        
      
        
        
# new code 
from rest_framework import serializers
from .models import LoanLead


class LoanLeadCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = LoanLead

        fields = [
            "name",
            "mobile",
            "pincode",
            "category_id",
            "bank_id",
            "loan_amount",
        ]

    def create(self, validated_data):

        user = self.context["request"].user

        validated_data["created_by"] = user

        if hasattr(user, "agent_profile"):
            validated_data["agent"] = user.agent_profile

        return super().create(validated_data)
    
    
# class LoanLeadListSerializer(serializers.ModelSerializer):

#     class Meta:

#         model = LoanLead

#         fields = [
#             "id",
#             "name",
#             "mobile",
#             "status",
#             "loan_amount",
#             "approved_amount",
#             "disbursed_amount",
#             "created_at",
#         ]
        
        
class LoanLeadDetailSerializer(serializers.ModelSerializer):

    class Meta:

        model = LoanLead

        fields = "__all__"
        
        
class LoanLeadUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = LoanLead

        fields = [
            "status",
            "approved_amount",
            "disbursed_amount",
            "status_message",
            "provider_response",
            "redirect_url",
        ]
        
        
        
# serializers.py

from rest_framework import serializers
from .models import LoanLead


class LoanLeadListSerializer(serializers.ModelSerializer):

    class Meta:
        model = LoanLead
        fields = [
            "id",
            "name",
            "mobile",
            "loan_amount",
            "approved_amount",
            "disbursed_amount",
            "category_code",
            "provider_response",
            "bank_name",
            "status",
            "created_at",
        ]