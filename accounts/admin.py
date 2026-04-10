from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    model = User

    # =====================
    # LIST
    # =====================

    list_display = (
        "id",
        "username",
        "email",
        "mobile",
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
        "is_verified",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "phoneNo",
    )

    ordering = ("-id",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
    )

    # =====================
    # EDIT USER
    # =====================

    fieldsets = (

        ("Login Info", {
            "fields": (
                "username",
                "email",
                "mobile",
                "password",
            )
        }),

        ("Role Info", {
            "fields": (
                "role",
                "is_verified",
            )
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Dates", {
            "fields": (
                "last_login",
                "date_joined",
                "created_at",
                "updated_at",
            )
        }),
    )

    # =====================
    # ADD USER
    # =====================

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "mobile",
                "password1",
                "password2",
                "role",
                "is_verified",
                "is_staff",
                "is_superuser",
            ),
        }),
    )