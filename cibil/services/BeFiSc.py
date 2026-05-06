import requests
import logging
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SmartAuthClient:

    def __init__(self):
        self.base_url = settings.BUREAU_B_BASE_URL
        self.authkey = settings.BUREAU_B_AUTHKEY
        self.session = self._create_session()

        # ✅ Endpoint Mapping
        self.endpoints = {
            "cibil_advanced": "/TILJ",
            "only_score": "/R2RZ/v3",
        }

        # ✅ Payload Builders Mapping
        self.payload_builders = {
            "cibil_advanced": self._build_cibil_payload,
            "only_score": self._build_pan_payload,
        }

    def _create_session(self):
        session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)

        return session

    # =========================
    # 🔧 Payload Builders
    # =========================

    def _build_cibil_payload(self, name, mobile, pan):
        return {
            "name": name,
            "mobile": mobile,
            "pan": pan,
            "consent_text": "We confirm obtaining valid customer consent to access/process their mobile/pan/name data. Consent remains valid, informed, and unwithdrawn." , 
            "consent": "Y",
        }

    def _build_pan_payload(self, mobile, pan):
        return {
            "pan": pan,
            "mobile": mobile,
            "consent_text": "We confirm obtaining valid customer consent to access/process their mobile/pan data. Consent remains valid, informed, and unwithdrawn.", 
            "consent": "Y",
        }

    # =========================
    # 🔗 URL Builder
    # =========================

    def _get_url(self, service_type):
        endpoint = self.endpoints.get(service_type)
        if not endpoint:
            raise ValueError(f"Invalid service type: {service_type}")
        return f"{self.base_url}{endpoint}"

    # =========================
    # 🚀 MAIN FUNCTION
    # =========================

    def call_api(self, service_type, name=None, mobile=None, pan=None):
        try:
            url = self._get_url(service_type)

            payload_builder = self.payload_builders.get(service_type)
            if not payload_builder:
                raise ValueError("Payload builder not found")
            
            if service_type == "only_score":
                payload = payload_builder(mobile, pan)
            else:
                payload = payload_builder(name, mobile, pan)

            # payload = payload_builder(name, mobile, pan)

            headers = {
                "authkey": self.authkey,
                "Content-Type": "application/json"
            }

            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )

            logger.info(f"{service_type} Response: {response.text}")
            
            
            if response.status_code == 504:
                return {
                    "status": False,
                    "message": "Bureau server timeout. Please try again later."
                }

            if response.status_code != 200:
                return {
                    "status": False,
                    "message": f"HTTP Error {response.status_code}"
                }

            data = response.json()
            print("FULL API RESPONSE =>", data)

            if data.get("status") != 1:
                return {
                    "status": False,
                    "message": data.get("message", "Failed"),
                    "data": data
                }

            # =========================
            # 🎯 Response Parsing
            # =========================

            parsed_data = {}

            if service_type == "cibil_advanced":
                result = data.get("result", {})
                parsed_data["html_url"] = result.get("htmlUrl")

                try:
                    parsed_data["score"] = result["cibilData"]["GetCustomerAssetsResponse"]["GetCustomerAssetsSuccess"]["Asset"]["TrueLinkCreditReport"]["CreditScore"]["riskScore"]
                except Exception:
                    parsed_data["score"] = None

            elif service_type == "only_score":
                result = data.get("result", {})
                
                parsed_data = {
                    "full_name": result.get("full_name"),
                    "dob": result.get("dob"),
                    "gender": result.get("gender"),
                    "aadhaar_linked": result.get("aadhaar_linked"),
                    "fin_score": result.get("fin_score"),
                     "address": result.get("address"),
                }

            return {
                "status": True,
                "message": "Success",
                "txn_id": data.get("txn_id"),
                "data": parsed_data,
                "raw": data
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {str(e)}")
            return {
                "status": False,
                "message": "API request failed"
            }

        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            return {
                "status": False,
                "message": str(e)
            }