from django.db import models

# Create your models here.

# class GlobalPlan(models.Model):

#     title = models.CharField(max_length=100)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)

#     # 🔥 All services (CIBIL + KYC)
#     service_prices = models.JSONField(default=dict)

#     is_active = models.BooleanField(default=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.title} - ₹{self.amount}"