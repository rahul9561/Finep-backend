from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        AGENT = "agent", "Agent"
        CUSTOMER = "customer", "Customer"   # ✅ changed

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=13, blank=True, null=True)

    # 🔥 Unique User Code
    user_code = models.CharField(max_length=20, unique=True, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AGENT,
    )

    # 🔥 Customer belongs to Agent
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers"   # ✅ changed
    )

    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        if not self.user_code:
            self.user_code = self.generate_user_code()
        super().save(*args, **kwargs)

    def generate_user_code(self):
        prefix = (
            "ADM" if self.role == "admin"
            else "AG" if self.role == "agent"
            else "CUS"   # ✅ changed from EMP
        )

        while True:
            code = f"{prefix}{uuid.uuid4().hex[:8].upper()}"
            if not User.objects.filter(user_code=code).exists():
                return code

    def __str__(self):
        return f"{self.username} ({self.role})"