# loans/services/propelld_service.py

import requests
from django.conf import settings


class PropelldService:

    BASE = settings.PROPELLD_BASE_URL

    @staticmethod
    def headers():
        return {
            "client-id": settings.PROPELLD_CLIENT_ID,
            "client-secret": settings.PROPELLD_CLIENT_SECRET,
            "Content-Type": "application/json",
        }

    # ✅ CREATE QUOTE
    @classmethod
    def create_quote(cls, payload):

        url = f"{cls.BASE}/product/apply/generic"

        res = requests.post(
            url,
            json=payload,
            headers=cls.headers(),
            timeout=30
        )
        
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)

        return res.json()

    # ✅ APPROVE QUOTE
    @classmethod
    def approve_quote(cls, quote_id, approved=True):

        url = f"{cls.BASE}/quote/approve"

        payload = {
            "QuoteId": quote_id,
            "Approved": approved
        }

        res = requests.post(
            url,
            json=payload,
            headers=cls.headers(),
            timeout=30
        )

        return res.json()

    # ✅ EMI DETAILS
    @classmethod
    def emi_details(cls, course_id, loan_amount):

        url = f"{cls.BASE}/product/emi/table"

        payload = {
            "CourseId": int(course_id),
            "LoanAmount": int(loan_amount),
        }

        res = requests.post(
            url,
            json=payload,
            headers=cls.headers(),
            timeout=30
        )
        
        print("EMI URL:", url)
        print("EMI RES:", res.text)

        return res.json()