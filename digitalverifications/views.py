# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services.mobile360_service import Mobile360Service


class Mobile360APIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        mobile = request.data.get("mobile")

        if not mobile:
            return Response(
                {
                    "success": False,
                    "message": "Mobile number required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        result = Mobile360Service.check_mobile(
            user=request.user,
            mobile=mobile
        )

        if not result.get("success"):

            return Response(
                result,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result,
            status=status.HTTP_200_OK
        )