from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Wallet

User = get_user_model()


@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):

    if not created:
        return

    # ❌ Skip admin / staff
    if instance.is_superuser or instance.is_staff:
        return

    # ✅ Only for agent & customer
    if getattr(instance, "role", None) in ["agent", "customer"]:
        Wallet.objects.get_or_create(user=instance)