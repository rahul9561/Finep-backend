import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler("surepass.log")
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


class SurepassClient:

    def __init__(self):

        self.base_url = settings.SUREPASS_BASE_URL.rstrip("/")
        self.token = settings.SUREPASS_TOKEN

    # ---------------- HEADERS ---------------- #

    def _headers(self):

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    # ---------------- COMMON POST ---------------- #

    def post(self, endpoint, payload):

        url = f"{self.base_url}{endpoint}"

        logger.info(f"URL: {url}")
        logger.info(f"PAYLOAD: {payload}")

        try:
            r = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=30,
            )

            logger.info(f"STATUS: {r.status_code}")
            logger.info(f"RESPONSE: {r.text}")

            # if r.status_code != 200:
            #     return {
            #         "status": False,
            #         "http_status": r.status_code,
            #         "message": r.text,
            #     }

            # return r.json()
            try:
                data = r.json()
            except Exception:
                data = {"message": r.text}

            data["status_code"] = r.status_code

            return data

        except Exception as e:

            logger.error(f"ERROR: {str(e)}")

            return {
                "status": False,
                "message": str(e),
            }
    # ================= BANK =================
    # https://sandbox.surepass.io/api/v1/bank-verification/

    def bank_verification(self, id_number, ifsc):

        return self.post(
            "/bank-verification/",
            {
                "id_number": id_number,
                "ifsc": ifsc,
                "ifsc_details": True,
            },
        )

    # ================= PAN =================
    # https://sandbox.surepass.io/api/v1/pan/pan-verify

    def pan_verify(self, id_number, full_name, dob):

        return self.post(
            "/pan/pan-verify",
            {
                "id_number": id_number,
                "full_name": full_name,
                "dob": dob,
            },
        )

    # ================= AADHAAR =================
    # https://sandbox.surepass.io/api/v1/aadhaar-validation/aadhaar-validation

    def aadhaar_validation(self, id_number):

        return self.post(
            "/aadhaar-validation/aadhaar-validation",
            {
                "id_number": id_number,
            },
        )

    # ================= GST =================
    # https://sandbox.surepass.io/api/v1/corporate/gstin

    def gst_verify(self, id_number):

        return self.post(
            "/corporate/gstin",
            {
                "id_number": id_number,
            },
        )

    # ================= MSME =================
    # https://sandbox.surepass.io/api/v1/pan-to-msme/initialize

    # def pan_to_msme(self, pan):

    #     payload = {
    #         "pan": pan,
    #     }

    #     res = self.post("/pan-to-msme/initialize", payload)

    #     if not res or not res.get("success"):
    #         return {
    #             "success": False,
    #             "data": None,
    #             "message": res.get("message") if res else "API error",
    #         }

    #     return res
    def pan_to_msme(self, pan):

        # 🔥 STEP 1: Initialize
        init_res = self.post(
            "/pan-to-msme/initialize",
            {"pan": pan},
        )

        if not init_res or not init_res.get("success"):
            return init_res

        client_id = init_res.get("data", {}).get("client_id")

        if not client_id:
            return {
                "success": False,
                "message": "Client ID not found",
            }

        # 🔥 STEP 2: Status polling
        for _ in range(3):

            time.sleep(2)

            status_res = self.post(
                "/pan-to-msme/status",
                {"client_id": client_id},
            )

            if status_res.get("data") and status_res["data"].get("status") != "pending":
                return status_res

        return {
            "success": False,
            "message": "MSME data not ready yet",
        }

    # ================= RC =================
    # https://sandbox.surepass.io/api/v1/rc/vehicle-application-status

    def rc_verify(self, rc_number):
        return self.post(
            "/rc/rc-v2",
            {
                "id_number": rc_number,
                "enrich": True,
            },
        )

    # ================= ELECTRICITY =================
    # https://sandbox.surepass.io/api/v1/utility/electricity/

    def electricity_verify(self, id_number, operator_code):

        return self.post(
            "/utility/electricity/",
            {
                "id_number": id_number,
                "operator_code": operator_code,
            },
        )