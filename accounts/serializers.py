from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.AGENT   # ✅ default fix
        )
    
    
from django.db.models import Sum
from cibil.models import AgentPlan

class UserSerializer(serializers.ModelSerializer):

    wallet_balance = serializers.SerializerMethodField()
    plan_balance = serializers.SerializerMethodField()

    def get_wallet_balance(self, obj):
        if hasattr(obj, "wallet") and obj.wallet:
            return obj.wallet.balance
        return 0

    def get_plan_balance(self, obj):
        # ✅ Use enum (safe)
        if obj.role == obj.Role.AGENT:

            total = AgentPlan.objects.filter(
                agent=obj,
                is_active=True
            ).aggregate(total=Sum("remaining_balance"))["total"]

            return total or 0

        return None   # ✅ better than 0

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "mobile",
            "role",
            "user_code",
            "wallet_balance",
            "plan_balance",
            "is_blocked",   # ✅ add this
        ]
        
        
# accounts/serializers.py

from rest_framework import serializers
from .models import User


class CreateCustomerSerializer(serializers.ModelSerializer):   # ✅ renamed

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "mobile",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        creator = request.user

        # 🔥 Only admin or agent allowed
        if creator.role not in ["admin", "agent"]:
            raise serializers.ValidationError("Not allowed to create customer")  # ✅ changed

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            mobile=validated_data.get("mobile"),
            role="customer",             # ✅ changed
            created_by=creator           # same
        )

        return user
    
    
# serializers.py

from rest_framework import serializers
from .models import User



class UpdateCustomerSerializer(serializers.ModelSerializer):   # ✅ renamed

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "mobile",
            "is_verified",
        ]

    def validate_email(self, value):
        user = self.instance
        if User.objects.exclude(id=user.id).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_username(self, value):
        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_mobile(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone number must be numeric")
        return value