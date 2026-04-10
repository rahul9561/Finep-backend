# serializers.py — Production Ready
# Fixes:
#  • fetch_cibil_score was used but never imported → NameError on every create
#  • fetch_cibil_score returns (score, raw) tuple; was assigned as scalar → TypeError
#  • Cleaned up duplicate class/import blocks

from rest_framework import serializers

from eduloans.services.cibil_score import fetch_cibil_score  # FIX: was missing

from .models import (
    CoApplicant,
    EducationLoanApplication,
    HusbandDetails,
    PropertyDetails,
    StudentDetails,
)


# ─── Nested serializers ───────────────────────────────────────────────────────

class StudentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model   = StudentDetails
        exclude = ("application",)


class CoApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model   = CoApplicant
        exclude = ("application",)


class HusbandSerializer(serializers.ModelSerializer):
    class Meta:
        model   = HusbandDetails
        exclude = ("application",)


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model   = PropertyDetails
        exclude = ("application",)


# ─── Main application serializer ─────────────────────────────────────────────

class EducationLoanApplicationSerializer(serializers.ModelSerializer):
    student     = StudentDetailsSerializer(required=False)
    coapplicant = CoApplicantSerializer(required=False)
    husband     = HusbandSerializer(required=False)
    property    = PropertySerializer(required=False)  # noqa: A003

    class Meta:
        model  = EducationLoanApplication
        fields = "__all__"

    def create(self, validated_data):
        student_data  = validated_data.pop("student",     None)
        co_data       = validated_data.pop("coapplicant", None)
        husband_data  = validated_data.pop("husband",     None)
        property_data = validated_data.pop("property",    None)

        application = EducationLoanApplication.objects.create(**validated_data)

        # ── Student ──────────────────────────────────────────────────────────
        if student_data:
            student = StudentDetails.objects.create(
                application=application, **student_data
            )
            # Auto-fetch CIBIL if PAN + mobile are present
            try:
                pan    = student_data.get("pan_number")
                mobile = student_data.get("mobile")
                if pan and mobile:
                    # FIX: fetch_cibil_score returns (score, raw) — must unpack tuple
                    score, _ = fetch_cibil_score(
                        pan=pan,
                        mobile=mobile,
                        name=application.name,
                        gender=application.gender,
                    )
                    if score:
                        student.cibil_score = score
                        student.save(update_fields=["cibil_score"])
            except Exception as exc:
                print(f"[CIBIL AUTO-FETCH ERROR] {exc}")

        # ── Co-Applicant ─────────────────────────────────────────────────────
        if co_data:
            CoApplicant.objects.create(application=application, **co_data)

        # ── Husband / Spouse ─────────────────────────────────────────────────
        if husband_data:
            HusbandDetails.objects.create(application=application, **husband_data)

        # ── Property ─────────────────────────────────────────────────────────
        if property_data:
            PropertyDetails.objects.create(application=application, **property_data)

        return application


# ─── Admin serializer ─────────────────────────────────────────────────────────

class AdminEducationLoanSerializer(serializers.ModelSerializer):
    agent_name   = serializers.CharField(source="agent.user.name",   read_only=True)
    agent_mobile = serializers.CharField(source="agent.user.mobile", read_only=True)

    class Meta:
        model  = EducationLoanApplication
        fields = [
            "id",
            "name",
            "loan_type",
            "course",
            "country",
            "loan_amount",
            "gender",
            "marital_status",
            "created_at",
            "agent_name",
            "agent_mobile",
        ]