from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer
from .models import User


# -----------------------
# Register
# -----------------------

class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "User created",
                    "data": UserSerializer(user).data,
                }
            )

        return Response(serializer.errors, status=400)


# -----------------------
# Login JWT
# -----------------------

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import UserSerializer

User = get_user_model()


class LoginView(APIView):

    def post(self, request):

        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "status": False,
                    "message": "Email and password required"
                },
                status=400,
            )

        # email se user
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Invalid email"
                },
                status=400,
            )

        # authenticate using username
        user = authenticate(
            username=user_obj.username,
            password=password,
        )

        if not user:
            return Response(
                {
                    "status": False,
                    "message": "Invalid password"
                },
                status=400,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "status": True,
                "token": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,   # 🔥 ADD THIS
                },
            }
        )

# -----------------------
# Profile
# -----------------------

class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        return Response(
            {
                "status": True,
                "user": UserSerializer(user).data,
            }
        )
        
        
# accounts/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import CreateCustomerSerializer, UserSerializer   # ✅ updated


class CreateCustomerView(APIView):   # ✅ renamed

    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 🔥 Only admin or agent
        if request.user.role not in ["admin", "agent"]:
            return Response(
                {"status": False, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateCustomerSerializer(   # ✅ updated
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.save()

            return Response({
                "status": True,
                "message": "Customer created successfully",   # ✅ updated
                "data": UserSerializer(user).data
            })

        return Response(serializer.errors, status=400)
    
    
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from accounts.serializers import UserSerializer


class MyCustomersAPIView(APIView):   # ✅ renamed
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 🔥 Admin → all customers
        # if user.role == "admin":
        #     customers = User.objects.filter(role="customer")   # ✅ changed

        # # 🔥 Agent → only own customers
        # elif user.role == "agent":
        #     customers = User.objects.filter(
        #         role="customer",       # ✅ changed
        #         created_by=user
        #     )
        # use constants instead of string
        if user.role == User.Role.ADMIN:
            customers = User.objects.filter(role=User.Role.CUSTOMER)

        elif user.role == User.Role.AGENT:
            customers = User.objects.filter(
                role=User.Role.CUSTOMER,
                created_by=user
            )

        else:
            return Response(
                {"message": "Not allowed"},
                status=403
            )

        serializer = UserSerializer(customers, many=True)

        return Response({
            "status": True,
            "count": customers.count(),
            "data": serializer.data
        })
        
        
# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import User
from .serializers import UpdateCustomerSerializer   # ✅ updated


class UpdateCustomerAPIView(APIView):   # ✅ renamed

    permission_classes = [IsAuthenticated]

    def patch(self, request, customer_id):   # ✅ param renamed

        # 🔍 Get customer
        try:
            customer = User.objects.get(
                id=customer_id,
                role="customer"   # ✅ changed
            )
        except User.DoesNotExist:
            return Response(
                {"status": False, "message": "Customer not found"},   # ✅ updated
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # 🔐 Permission check
        if user.role == "admin":
            pass

        elif user.role == "agent":
            if customer.created_by != user:
                return Response(
                    {"status": False, "message": "You can only edit your customers"},  # ✅ updated
                    status=status.HTTP_403_FORBIDDEN
                )

        else:
            return Response(
                {"status": False, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✏️ Update fields
        serializer = UpdateCustomerSerializer(   # ✅ updated
            customer,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            # 🔒 Password update (secure)
            password = request.data.get("password")
            if password:
                customer.set_password(password)
                customer.save(update_fields=["password"])

            return Response({
                "status": True,
                "message": "Customer updated successfully",   # ✅ updated
                "data": serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class DeleteCustomerAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, customer_id):

        try:
            customer = User.objects.get(
                id=customer_id,
                role="customer"
            )
        except User.DoesNotExist:
            return Response(
                {"status": False, "message": "Customer not found"},
                status=404
            )

        user = request.user

        # 🔐 Permission check
        if user.role == "admin":
            pass

        elif user.role == "agent":
            if customer.created_by != user:
                return Response(
                    {
                        "status": False,
                        "message": "You can only delete your customers"
                    },
                    status=403
                )

        else:
            return Response(
                {"status": False, "message": "Permission denied"},
                status=403
            )

        # 🔥 DELETE
        customer.delete()

        return Response({
            "status": True,
            "message": "Customer deleted successfully"
        })
        
class ToggleBlockCustomerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, customer_id):

        try:
            customer = User.objects.get(
                id=customer_id,
                role=User.Role.CUSTOMER
            )
        except User.DoesNotExist:
            return Response(
                {"status": False, "message": "Customer not found"},
                status=404
            )

        user = request.user

        # 🔐 Permission check
        if user.role == User.Role.ADMIN:
            pass

        elif user.role == User.Role.AGENT:
            if customer.created_by != user:
                return Response(
                    {"status": False, "message": "Not allowed"},
                    status=403
                )
        else:
            return Response(
                {"status": False, "message": "Permission denied"},
                status=403
            )

        # 🔥 Toggle block
        customer.is_blocked = not customer.is_blocked
        customer.save(update_fields=["is_blocked"])

        return Response({
            "status": True,
            "message": "Customer blocked" if customer.is_blocked else "Customer unblocked",
            "is_blocked": customer.is_blocked
        })