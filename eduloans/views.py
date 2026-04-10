# views.py — Production Ready
# Fixes:
#  • Removed duplicate CoApplicantBankCheckView (stub overwrote real impl)
#  • Added permission_classes to StudentCibilCheckView
#  • Wrapped every EducationLoanApplication.objects.get() in try/except
#  • application_id is now fully optional in all CIBIL / verify views
#  • Added required-field validation to MSMEVerifyView & GSTVerifyView
#  • Converted request.data → dict() before storing in JSONField
#  • Cleaned up duplicate imports
#  • Consistent HTTP status codes throughout

from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from agent.models import Agent
from eduloans.services.bankclients import create_client, upload_statement
from eduloans.services.cibil_score import fetch_cibil_score

from .models import (
    EducationLoanApplication,
    SurepassLog,
    VerificationStatus,
)
from .serializers import (
    AdminEducationLoanSerializer,
    EducationLoanApplicationSerializer,
)
from .utils import send_loan_application_email


# ─── Shared helper ────────────────────────────────────────────────────────────

def _resolve_application(application_id):
    """
    Returns (app_or_None, err_response_or_None).
    Callers check: if err: return err
    A None app just means no ID was supplied — not an error.
    """
    if not application_id:
        return None, None
    try:
        return EducationLoanApplication.objects.get(id=application_id), None
    except (EducationLoanApplication.DoesNotExist, Exception):
        return None, Response(
            {"success": False, "message": "Application not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


# ─── CIBIL ────────────────────────────────────────────────────────────────────

class StudentCibilCheckView(APIView):
    """FIX: was missing permission_classes → unauthenticated endpoint."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pan            = request.data.get("pan")
        mobile         = request.data.get("mobile")
        name           = request.data.get("name")
        gender         = request.data.get("gender")
        application_id = request.data.get("application")

        if not pan or not mobile or not name:
            return Response(
                {"success": False, "message": "pan, mobile and name are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score, raw = fetch_cibil_score(pan, mobile, name, gender)

        # FIX: application_id is optional — CIBIL check works before application exists
        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            # FIX: dict(request.data) so QueryDict serialises into JSONField correctly
            SurepassLog.objects.create(
                application=app,
                service="cibil",
                request_data=dict(request.data),
                response_data=raw,
                status="success" if score else "failed",
            )
            if score:
                v, _ = VerificationStatus.objects.get_or_create(application=app)
                v.student_cibil = True
                v.save()

        if not score:
            return Response(
                {"success": False, "message": "Unable to fetch CIBIL score.", "data": raw},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "score": score, "data": raw})


class CoApplicantCibilCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pan            = request.data.get("pan")
        mobile         = request.data.get("mobile")
        name           = request.data.get("name")
        gender         = request.data.get("gender")
        application_id = request.data.get("application")

        if not pan or not mobile or not name:
            return Response(
                {"success": False, "message": "pan, mobile and name are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score, raw = fetch_cibil_score(pan=pan, mobile=mobile, name=name, gender=gender)

        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            SurepassLog.objects.create(
                application=app,
                service="co_cibil",
                request_data=dict(request.data),
                response_data=raw,
                status="success" if score else "failed",
            )
            if score:
                v, _ = VerificationStatus.objects.get_or_create(application=app)
                v.co_cibil = True
                v.save()

        if not score:
            return Response(
                {"success": False, "message": "Unable to fetch CIBIL score.", "data": raw},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "score": score, "data": raw})


# ─── Bank Statement ───────────────────────────────────────────────────────────

class CoApplicantBankCheckView(APIView):
    """
    FIX: was defined TWICE — the second stub definition silently overwrote
    the real implementation that calls create_client / upload_statement.
    Removed the stub; kept and hardened the real one.
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request):
        name   = request.data.get("name")
        mobile = request.data.get("mobile")
        file   = request.FILES.get("file")

        if not file:
            return Response(
                {"success": False, "message": "file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not name or not mobile:
            return Response(
                {"success": False, "message": "name and mobile are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client    = create_client(name, mobile)
        client_id = client.get("data", {}).get("client_id")

        if not client_id:
            return Response(
                {"success": False, "message": "Failed to create client.", "data": client},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = upload_statement(client_id, file)
        return Response(result)


# ─── Document Verifications ───────────────────────────────────────────────────

class AadhaarVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        aadhaar        = request.data.get("aadhaar")
        application_id = request.data.get("application")

        if not aadhaar:
            return Response(
                {"error": "aadhaar is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from eduloans.services.aadhaar import verify_aadhaar
        data = verify_aadhaar(aadhaar)

        # FIX: was bare .get() with no error handling
        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            SurepassLog.objects.create(
                application=app,
                service="aadhaar",
                request_data=dict(request.data),
                response_data=data,
                status="success",
            )
            v, _ = VerificationStatus.objects.get_or_create(application=app)
            v.aadhaar_verified = True
            v.save()

        return Response(data)


class PanVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pan            = request.data.get("pan")
        name           = request.data.get("name")
        dob            = request.data.get("dob")
        application_id = request.data.get("application")

        if not pan:
            return Response(
                {"error": "pan is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from eduloans.services.pan import verify_pan
        data = verify_pan(pan, name, dob)

        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            SurepassLog.objects.create(
                application=app,
                service="pan",
                request_data=dict(request.data),
                response_data=data,
                status="success" if data else "failed",
            )
            v, _ = VerificationStatus.objects.get_or_create(application=app)
            v.pan_verified = True
            v.save()

        return Response(data)


class ITRVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pan            = request.data.get("pan")
        application_id = request.data.get("application")

        if not pan:
            return Response(
                {"error": "pan is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from eduloans.services.itr import verify_itr
        data = verify_itr(pan)

        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            SurepassLog.objects.create(
                application=app,
                service="itr",
                request_data=dict(request.data),
                response_data=data,
                status="success" if data else "failed",
            )
            v, _ = VerificationStatus.objects.get_or_create(application=app)
            v.itr_verified = True
            v.save()

        return Response(data)


class MSMEVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pan            = request.data.get("pan")
        application_id = request.data.get("application")

        # FIX: was missing required-field check entirely
        if not pan:
            return Response(
                {"error": "pan is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from eduloans.services.msme import verify_msme
        data = verify_msme(pan)

        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            v, _ = VerificationStatus.objects.get_or_create(application=app)
            v.msme_verified = True
            v.save()

        return Response(data)


class GSTVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        gst            = request.data.get("gst")
        application_id = request.data.get("application")

        # FIX: was missing required-field check entirely
        if not gst:
            return Response(
                {"error": "gst is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from eduloans.services.gst import verify_gst
        data = verify_gst(gst)

        app, err = _resolve_application(application_id)
        if err:
            return err

        if app:
            v, _ = VerificationStatus.objects.get_or_create(application=app)
            v.gst_verified = True
            v.save()

        return Response(data)


# ─── Application Submit ───────────────────────────────────────────────────────

class EducationLoanApplyView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return Response(
                {"error": "Agent profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data        = request.data.copy()
        data["agent"] = agent.id

        # Pre-validate CIBIL scores before hitting the serializer
        try:
            student_score = int(data.get("student.cibil_score") or 0)
            if student_score and student_score < 650:
                return Response(
                    {"error": "Student CIBIL score is below 650. Application cannot proceed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            pass

        try:
            co_score = int(data.get("coapplicant.cibil_score") or 0)
            if co_score and co_score < 650:
                return Response(
                    {"error": "Co-applicant CIBIL score is below 650. Application cannot proceed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            pass

        serializer = EducationLoanApplicationSerializer(data=data)
        if serializer.is_valid():
            loan_obj = serializer.save()
            student  = getattr(loan_obj, "student", None)
            send_loan_application_email(loan_obj, agent, student)
            return Response(
                {"message": "Application submitted successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Admin List ───────────────────────────────────────────────────────────────

class LoanPagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = "page_size"
    max_page_size         = 100


class AdminEducationLoanListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = AdminEducationLoanSerializer
    pagination_class   = LoanPagination

    def get_queryset(self):
        qs = EducationLoanApplication.objects.select_related(
            "agent", "agent__user"
        )

        search     = self.request.GET.get("search")
        loan_type  = self.request.GET.get("loan_type")
        start_date = self.request.GET.get("start_date")
        end_date   = self.request.GET.get("end_date")

        if search:
            qs = qs.filter(
                Q(name__icontains=search)              |
                Q(course__icontains=search)            |
                Q(country__icontains=search)           |
                Q(agent__user__name__icontains=search) |
                Q(agent__user__mobile__icontains=search)
            )
        if loan_type:
            qs = qs.filter(loan_type=loan_type)
        if start_date and end_date:
            qs = qs.filter(created_at__date__range=[start_date, end_date])

        return qs.order_by("-created_at")


# ─── Utility ──────────────────────────────────────────────────────────────────

def update_final_status(app):
    """FIX: wrapped in try/except — crashes if VerificationStatus doesn't exist yet."""
    try:
        v = app.verification
    except VerificationStatus.DoesNotExist:
        return

    v.final_status = (
        "approved"
        if (v.student_cibil and v.bank_verified and v.pan_verified)
        else "pending"
    )
    v.save()
    
    
class DigiLockerEducationCheck(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        application_id = request.data.get("application")

        if not application_id:
            return Response(
                {"error": "application required"},
                status=400,
            )

        from eduloans.services.digilocker_docs import (
            get_digilocker_docs,
            verify_education,
        )

        data = get_digilocker_docs()

        docs = data.get("data", {}).get("documents", [])

        ok = verify_education(docs)

        try:
            app = EducationLoanApplication.objects.get(
                id=application_id
            )
        except EducationLoanApplication.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=404,
            )

        # ✅ log save
        SurepassLog.objects.create(
            application=app,
            service="digilocker",
            request_data=dict(request.data),
            response_data=data,
            status="success" if ok else "failed",
        )

        # ✅ verification status
        v, _ = VerificationStatus.objects.get_or_create(
            application=app
        )

        if ok:
            v.education_verified = True

        v.save()

        return Response({
            "success": ok,
            "documents": docs
        })
        
        


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from eduloans.services.death_verify import verify_death


class DeathVerifyAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serial = request.data.get("serial_number")
        state = request.data.get("state_name")

        if not serial or not state:
            return Response(
                {"error": "serial_number & state_name required"},
                status=400,
            )

        data = verify_death(
            serial_number=serial,
            state_name=state,
        )

        return Response(data)