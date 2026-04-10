# from django.db import models
# from django.conf import settings

# # Create your models here.
# class BankStatement(models.Model):

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

#     file = models.FileField(upload_to="statements/")

#     uploaded_at = models.DateTimeField(auto_now_add=True)