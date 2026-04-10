from django.contrib import admin
from .models import *
from django.utils.html import format_html


@admin.register(CibilReport)
class CibilReportAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "mobile",
        "pan",
        "report_type",
        "status",
        "agent",
        "created_at",
        "pdf_link",
    )

    list_filter = (
        "status",
        "report_type",
        "created_at",
        "agent",
    )

    search_fields = (
        "name",
        "mobile",
        "pan",
        "agent__username",
        "agent__email",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25

    date_hierarchy = "created_at"


    def pdf_link(self, obj):
        if obj.report_pdf:
            return format_html(
                '<a href="{}" target="_blank">View</a>',
                obj.report_pdf.url
            )
        return "-"

    pdf_link.allow_tags = True
    pdf_link.short_description = "PDF"
    
    
    
# cibil/admin.py

from django.contrib import admin

from .models import (
    CibilReport,
    RechargePlan,
    AgentPlan,
    PlanUsage,
)





# =========================
# RECHARGE PLAN
# =========================

@admin.register(RechargePlan)
class RechargePlanAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "plan_type",
        "amount",
        "min_amount",
        "max_amount",
        "cibil_price",
        "experian_price",
        "crif_price",
        "equifax_price",
        "is_active",
        "created_at",
    )

    list_filter = (
        "plan_type",
        "is_active",
    )

    search_fields = ("title",)

    readonly_fields = ("created_at",)


# =========================
# AGENT PLAN
# =========================

@admin.register(AgentPlan)
class AgentPlanAdmin(admin.ModelAdmin):

    list_display = (
        "agent",
        "plan",
        "remaining_balance",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "agent__username",
        "plan__title",
    )


# =========================
# PLAN USAGE
# =========================

@admin.register(PlanUsage)
class PlanUsageAdmin(admin.ModelAdmin):

    list_display = (
        "agent",
        "service",
        "price",
        "created_at",
    )

    list_filter = (
        "service",
        "created_at",
    )

    search_fields = (
        "agent__username",
        "service",
    )
    
    
admin.site.register(AgentCibilPricing)