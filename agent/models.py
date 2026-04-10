# agent/models/agent.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class Agent(models.Model):
    """
    Agent profile linked with Django User.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="agent_profile"
    )

    # Auto-generated business ID
    agent_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,         # ✅ allow empty in admin
        editable=False      # ✅ prevent manual editing
    )

    mobile = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r"^[0-9]{10,15}$",
                message="Enter a valid mobile number."
            )
        ]
    )

    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    joining_date = models.DateField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["agent_code"]
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

    def __str__(self):
        return f"{self.agent_code} - {self.user.get_username()}"

    # 🔥 Safe auto-generate agent code
    def save(self, *args, **kwargs):
        if not self.agent_code:
            last_agent = Agent.objects.order_by("-id").first()
            next_id = (last_agent.id + 1) if last_agent else 1
            self.agent_code = f"AGT{next_id:04d}"
        super().save(*args, **kwargs)




class PartnerApplication(models.Model):
    full_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    business_name = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    services = models.JSONField()
    status = models.CharField(default="PENDING", max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)