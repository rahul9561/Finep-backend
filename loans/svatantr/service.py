from loans.models import LoanLead
from loans.svatantr.client import SvatantrClient
from datetime import datetime, timedelta


class LoanService:

    def create_lead(self, user, data):

        agent = None

        if hasattr(user, "agent_profile"):
            agent = user.agent_profile

        lead = LoanLead.objects.create(
            name=data["name"],
            mobile=data["mobile"],
            pincode=data["pincode"],
            category_id=data["categoryId"],
            category_code=data["categoryCode"],
            bank_name=data.get("bankName", ""),
            bank_id=data["bankId"],
            monthly_salary=data.get(
                "salary",
                data.get("income", 0)
            ),
            # loan_amount=data.get("loan_amount", 0),
            loan_amount=data.get("loan_amount") or 0,
            created_by=user,
            agent=agent,
            provider_name="SVATANTR",
            status="CREATED",
        )

        client = SvatantrClient()

        try:

            payload = {
                "name": data["name"],
                "mobileNo": data["mobile"],
                "categoryCode": data["categoryCode"],
                "bankId": data["bankId"],
                "income": str(
                    data.get("income")
                    or data.get("salary")
                    or 0
                ),
                "pinCode": data["pincode"],
                "state": data.get("state", "Punjab"),
            }

            response = client.create_lead(payload)

            lead.provider_response = response

            if response.get("success"):

                lead.status = "SENT"

                data_block = response.get("data", {})

                lead.redirect_url = data_block.get(
                    "redirectionUrl"
                )

                provider_id = (
                    data_block.get("result", {})
                    .get("_id")
                )

                if provider_id:
                    lead.provider_lead_id = str(provider_id)

                lead.is_complete = False

            else:

                lead.status = "FAILED"

                lead.status_message = response.get(
                    "message",
                    "Provider error"
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

            return lead
        
        
from loans.models import LoanLead
from loans.svatantr.client import SvatantrClient
from datetime import datetime, timedelta


class SvatantrSyncService:

    def sync(self, limit=50):

        client = SvatantrClient()

        start = (
            datetime.today() - timedelta(days=30)
        ).strftime("%Y-%m-%d")

        end = datetime.today().strftime("%Y-%m-%d")

        statuses = [
            "APPROVED",
            "SANCTIONED",
            "DISBURSED",
            "POSITIVE",
            "REJECTED",
            "PENDING",
        ]

        total = 0
        updated = 0

        for status in statuses:

            skip = 0

            while True:

                data = client.get_mis(
                    skip=skip,
                    limit=limit,
                    start=start,
                    end=end,
                    status=status,
                )

                data_block = data.get("data")

                if not data_block:
                    break

                results = data_block.get("result", [])

                if not results:
                    break

                for item in results:

                    total += 1

                    provider_id = str(item.get("_id"))

                    lead = LoanLead.objects.filter(
                        provider_lead_id=provider_id
                    ).first()

                    if not lead:
                        continue

                    updated += 1

                    tele_status = item.get("statusByTeleCaller")
                    is_complete = item.get("isTrxnComplete", False)

                    if tele_status == "POSITIVE":
                        lead.status = "PROCESSING"

                    elif tele_status == "APPROVED":
                        lead.status = "APPROVED"

                    elif tele_status == "SANCTIONED":
                        lead.status = "SANCTIONED"

                    elif tele_status == "DISBURSED":
                        lead.status = "DISBURSED"

                    elif tele_status == "REJECTED":
                        lead.status = "REJECTED"

                    if is_complete:
                        lead.status = "COMPLETED"
                        lead.is_complete = True

                    lead.telecaller_status = tele_status
                    lead.bank_name = item.get("bankName")
                    lead.application_no = item.get("applicationNo")
                    lead.provider_response = item

                    lead.save()

                skip += limit

        result = {
            "total": total,
            "updated": updated,
        }
        
        SyncLog.objects.create(
            service="SVATANTR",
            total=total,
            updated=updated,
            status="SUCCESS",
        )

        return result
    
    
    def get_mis_data(self, skip, limit, status, start, end):

        client = SvatantrClient()

        data = client.get_mis(
            skip=skip,
            limit=limit,
            status=status,
            start=start,
            end=end,
        )

        return data