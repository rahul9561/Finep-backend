# # services/models.py
# import uuid
# from django.db import models
# from django.conf import settings
# from django.utils import timezone

# class Service(models.Model):
#     SERVICE_TYPES = [
#         ("cibil", "CIBIL"),
#         ("kyc", "KYC"),
#         ("bank", "Bank"),
#     ]

#     name = models.CharField(max_length=100)  
#     code = models.CharField(max_length=50, unique=True)  
#     service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)

#     cost_price = models.DecimalField(max_digits=10, decimal_places=2)

#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name
    
    
# class AgentServicePricing(models.Model):
#     agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     service = models.ForeignKey(Service, on_delete=models.CASCADE)

#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     class Meta:
#         unique_together = ["agent", "service"]
        
        
# class RechargePlan(models.Model):
#     PLAN_TYPE = (
#         ("FIXED", "Fixed"),
#     )

#     title = models.CharField(max_length=200)   # ₹25K Plan
#     amount = models.DecimalField(max_digits=10, decimal_places=2)

#     # 🔥 important
#     discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

#     is_active = models.BooleanField(default=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.title} - ₹{self.amount}"