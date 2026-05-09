# services/esign_client.py

import requests
from django.conf import settings


class SurepassESignClient:
    BASE_URL = "https://kyc-api.surepass.app/api/v1/esign"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
            "Content-Type": "application/json"
        }

    # =========================================
    # UPLOAD PDF
    # =========================================
    def upload_pdf(self, client_id, pdf_link):
        url = f"{self.BASE_URL}/upload-pdf"

        payload = {
            "client_id": client_id,
            "link": pdf_link
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers
        )

        return response.json()

    # =========================================
    # INITIALIZE ESIGN
    # =========================================
    def initialize_esign(
        self,
        client_id,
        callback_url,
        full_name,
        mobile_number,
        email,
        stamp_state="Maharashtra",
        stamp_amount=100
    ):

        url = f"{self.BASE_URL}/initialize"

        payload = {
            "client_id": client_id,
            "pdf_pre_uploaded": False,
            "callback_url": callback_url,

            "config": {
                "accept_selfie": True,
                "allow_selfie_upload": True,
                "accept_virtual_sign": True,
                "track_location": True,
                "auth_mode": "1",
                "reason": "Loan Agreement",

                "positions": {
                    "1": [
                        {
                            "x": 10,
                            "y": 20
                        }
                    ]
                },

                "stamp_paper_amount": stamp_amount,
                "stamp_paper_state": stamp_state,

                "stamp_data": {
                    "Name": full_name,
                    "Email": email,
                    "Mobile": mobile_number
                }
            },

            "prefill_options": {
                "full_name": full_name,
                "mobile_number": mobile_number,
                "user_email": email
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers
        )

        return response.json()

    # =========================================
    # GET STATUS
    # =========================================
    def get_status(self, request_id):
        url = f"{self.BASE_URL}/status/{request_id}"

        response = requests.get(
            url,
            headers=self.headers
        )

        return response.json()

    # =========================================
    # GET SIGNED DOCUMENT
    # =========================================
    def get_signed_document(self, request_id):
        url = f"{self.BASE_URL}/get-signed-document/{request_id}"

        response = requests.get(
            url,
            headers=self.headers
        )

        return response.json()