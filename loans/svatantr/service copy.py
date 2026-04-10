from django.db import transaction

from loans.models import LoanLead
from loans.svatantr.client import SvatantrClient


class LoanService:

    def create_lead(self, user, data):

        client = SvatantrClient()

        with transaction.atomic():

            agent = None

            if hasattr(user, "agent_profile"):
                agent = user.agent_profile

            # -----------------------------
            # CREATE LOCAL LEAD
            # -----------------------------

            lead = LoanLead.objects.create(

                name=data["name"],
                mobile=data["mobile"],
                pincode=data["pincode"],

                category_id=data["categoryId"],
                bank_id=data["bankId"],

                loan_amount=data.get("loan_amount"),

                created_by=user,
                agent=agent,

                provider_name="SVATANTR",

                status="CREATED",
            )

            try:

                # -----------------------------
                # GET JOURNEY
                # -----------------------------

                journey = client.get_journey(
                    category_id=data["categoryId"]
                )

                required_fields = journey["data"].get(
                    "requiredFields", []
                )

                # -----------------------------
                # BUILD PAYLOAD
                # -----------------------------

                payload = {

                    "name": data["name"],
                    "mobile": data["mobile"],
                    "pincode": data["pincode"],

                    "bankId": data["bankId"],
                    "categoryId": data["categoryId"],
                }

                # -----------------------------
                # REQUIRED FIELDS
                # -----------------------------

                if "VehilceNo" in required_fields:
                    payload["VehilceNo"] = data.get(
                        "VehilceNo", ""
                    )

                if "DocumentLink" in required_fields:
                    payload["DocumentLink"] = data.get(
                        "DocumentLink", ""
                    )

                # -----------------------------
                # CALL SVATANTR
                # -----------------------------

                response = client.create_lead(payload)

                lead.provider_response = response

                lead.status = "SENT"

                if response.get("data"):

                    lead.redirect_url = response["data"].get(
                        "redirectUrl"
                    )

                    lead.provider_lead_id = response["data"].get(
                        "_id"
                    )

                lead.save()

                return lead

            except Exception as e:

                lead.status = "FAILED"

                lead.status_message = str(e)

                lead.provider_response = {
                    "error": str(e)
                }

                lead.save()

                raise