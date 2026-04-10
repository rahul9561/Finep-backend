from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("me/", ProfileView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path("create-customer/", CreateCustomerView.as_view()),
    path("customers/my/", MyCustomersAPIView.as_view()),
    path("customers/update/<int:customer_id>/", UpdateCustomerAPIView.as_view()),
    path("customers/delete/<int:customer_id>/", DeleteCustomerAPIView.as_view()),
     path("customer/block/<int:customer_id>/", ToggleBlockCustomerAPIView.as_view(), name="block-customer"),
]