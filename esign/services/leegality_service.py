# services/leegality_service.py

import requests

from django.conf import settings


class LeegalityService:

    BASE_URL_V3 = "https://app1.leegality.com/api/v3.0"

    BASE_URL_V33 = "https://app1.leegality.com/api/v3.3"

    def __init__(self):

        self.headers = {
            "X-Auth-Token": settings.LEEGALITY_AUTH_TOKEN,
            "Content-Type": "application/json"
        }

    # =====================================
    # CREATE SIGN REQUEST
    # =====================================

    def create_sign_request(
        self,
        file_name,
        base64_file,
        signer_name,
        signer_email,
        signer_phone,
        irn="ORDER_1001"
    ):

        payload = {

            "profileId": settings.LEEGALITY_PROFILE_ID,

            "file": {
                "name": file_name,
                "file": base64_file
            },

            "invitees": [
                {
                    "name": signer_name,
                    "email": signer_email,
                    "phone": signer_phone,
                    "inviteType": "SIGNER",
                    # "signatureType": "VIRTUAL_SIGN"
                    "signatureType": "AADHAAR_ESIGN"
                }
            ],

            "irn": irn
        }

        try:

            response = requests.post(

                f"{self.BASE_URL_V3}/sign/request",

                json=payload,

                headers=self.headers,

                timeout=60
            )

            print("CREATE SIGN STATUS:")
            print(response.status_code)

            print("CREATE SIGN RESPONSE:")
            print(response.text)

            return {

                "status_code": response.status_code,

                "data": response.json()
            }

        except requests.exceptions.RequestException as e:

            print("LEEGALITY ERROR:")
            print(str(e))

            return {

                "status_code": 500,

                "error": str(e)
            }

    # =====================================
    # FETCH DOCUMENT DETAILS
    # =====================================

    def fetch_document_details(
        self,
        document_id
    ):

        try:

            response = requests.get(

                f"{self.BASE_URL_V33}/document/details",

                params={
                    "documentId": document_id
                },

                headers=self.headers,

                timeout=60
            )

            print("FETCH DOCUMENT STATUS:")
            print(response.status_code)

            print("FETCH DOCUMENT RESPONSE:")
            print(response.text)

            return {

                "status_code": response.status_code,

                "data": response.json()
            }

        except requests.exceptions.RequestException as e:

            print("FETCH DOCUMENT ERROR:")
            print(str(e))

            return {

                "status_code": 500,

                "error": str(e)
            }