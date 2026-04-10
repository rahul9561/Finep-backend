
# from django.db import models
# from django.conf import settings


# class APILog(models.Model):

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

#     service = models.CharField(max_length=100)

#     request_data = models.JSONField(null=True, blank=True)

#     response_data = models.JSONField(null=True, blank=True)

#     status = models.CharField(max_length=20)

#     created_at = models.DateTimeField(auto_now_add=True)