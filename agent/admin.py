# agent/admin.py

from django.contrib import admin
from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("user", "agent_code", "mobile", "email", "is_active")
    search_fields = ("user__username", "agent_code", "mobile", "email")
    list_filter = ("is_active",)
    ordering = ("-joining_date",)

    readonly_fields = ("agent_code",)  # 👈 show but cannot edit
