from django.contrib import admin
from .models import (
    LoanApplication,
    PropelldWebhookLog,
    LoanStatusHistory,
    LoanLead,
    SyncLog,
)


# -----------------------------
# LoanApplication
# -----------------------------
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "first_name",
        "mobile",
        "loan_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "first_name",
        "mobile",
        "reference_number",
        "propelld_application_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# -----------------------------
# Webhook Log
# -----------------------------
@admin.register(PropelldWebhookLog)
class PropelldWebhookLogAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "event",
        "application_id",
        "created_at",
    )

    search_fields = (
        "event",
        "application_id",
    )

    readonly_fields = (
        "payload",
        "created_at",
    )


# -----------------------------
# Status History
# -----------------------------
@admin.register(LoanStatusHistory)
class LoanStatusHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "loan",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "loan__id",
        "status",
    )


# -----------------------------
# Loan Lead
# -----------------------------
@admin.register(LoanLead)
class LoanLeadAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "mobile",
        "provider_name",
        "loan_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "provider_name",
        "created_at",
    )

    search_fields = (
        "name",
        "mobile",
        "provider_lead_id",
        "application_no",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# -----------------------------
# Sync Log
# -----------------------------
@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "service",
        "total",
        "updated",
        "status",
        "created_at",
    )

    list_filter = (
        "service",
        "status",
    )

    search_fields = (
        "service",
        "message",
    )

    readonly_fields = (
        "created_at",
    )