from django.contrib import admin
from .models import (
    BankVerificationReport,
    PanVerificationReport,
    AadhaarValidationReport,
    GSTReport,
    MSMEReport,
    RCReport,
    ElectricityReport,
)


# =========================
# BANK
# =========================

@admin.register(BankVerificationReport)
class BankVerificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "id_number",
        "ifsc",
        "created_at",
    )

    search_fields = (
        "id_number",
        "ifsc",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )


# =========================
# PAN
# =========================

@admin.register(PanVerificationReport)
class PanVerificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "pan_number",
        "full_name",
        "dob",
        "created_at",
    )

    search_fields = (
        "pan_number",
        "full_name",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )


# =========================
# AADHAAR
# =========================

@admin.register(AadhaarValidationReport)
class AadhaarValidationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "aadhaar_number",
        "created_at",
    )

    search_fields = (
        "aadhaar_number",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )


# =========================
# GST
# =========================

@admin.register(GSTReport)
class GSTAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "gst_number",
        "created_at",
    )

    search_fields = (
        "gst_number",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )


# =========================
# MSME
# =========================

@admin.register(MSMEReport)
class MSMEAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "pan",
        "created_at",
    )

    search_fields = (
        "pan",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )


# =========================
# RC
# =========================

@admin.register(RCReport)
class RCAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "rc_number",
        "created_at",
    )

    search_fields = (
        "rc_number",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )


# =========================
# ELECTRICITY
# =========================

@admin.register(ElectricityReport)
class ElectricityAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "id_number",
        "operator_code",
        "created_at",
    )

    search_fields = (
        "id_number",
        "operator_code",
        "user__username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "response",
        "created_at",
    )