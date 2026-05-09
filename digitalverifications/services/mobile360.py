# services/mobile360.py

import json
import logging

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


BASE_URL = "https://fraud-check.befisc.com"


class SmartAuthClient:

    ENDPOINT = "/mobile-360"

    CONSENT_TEXT = (
        "We confirm obtaining valid customer consent "
        "to access/process their mobile data. "
        "Consent remains valid, informed, and unwithdrawn."
    )

    def __init__(self):

        self.base_url = BASE_URL
        self.authkey = settings.BUREAU_B_AUTHKEY
        self.session = self._create_session()

    # =====================================================
    # SESSION
    # =====================================================
    def _create_session(self):

        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    # =====================================================
    # HEADERS
    # =====================================================
    def _get_headers(self):

        return {
            "authkey": self.authkey,
            "Content-Type": "application/json",
        }

    # =====================================================
    # PAYLOAD
    # =====================================================
    def _build_payload(self, mobile):

        return {
            "mobile": str(mobile),
            "consent": "Y",
            "consent_text": self.CONSENT_TEXT,
        }

    # =====================================================
    # MAIN API
    # =====================================================
    def call_api(self, mobile):

        try:

            url = f"{self.base_url}{self.ENDPOINT}"

            headers = self._get_headers()

            payload = self._build_payload(mobile)

            logger.info("=" * 60)
            logger.info("MOBILE360 API REQUEST STARTED")
            logger.info("=" * 60)

            logger.info(f"URL: {url}")

            logger.info(
                f"HEADERS: {json.dumps(headers, indent=2)}"
            )

            logger.info(
                f"PAYLOAD: {json.dumps(payload, indent=2)}"
            )

            response = self.session.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=60,
            )

            logger.info("=" * 60)
            logger.info("MOBILE360 API RESPONSE")
            logger.info("=" * 60)

            logger.info(f"STATUS CODE: {response.status_code}")

            logger.info(f"RAW RESPONSE: {response.text}")

            # =====================================================
            # HTTP ERROR
            # =====================================================
            if response.status_code != 200:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = {}

                return {
                    "status": False,
                    "message": error_data.get(
                        "message",
                        f"HTTP Error {response.status_code}"
                    ),
                    "raw": response.text,
                }

            # =====================================================
            # JSON RESPONSE
            # =====================================================
            try:
                data = response.json()

            except ValueError:

                return {
                    "status": False,
                    "message": "Invalid JSON response",
                    "raw": response.text,
                }

            # =====================================================
            # API FAILED
            # =====================================================
            if data.get("status") != 1:

                return {
                    "status": False,
                    "message": data.get("message", "API Failed"),
                    "raw": data,
                }

            # =====================================================
            # FULL RESULT DATA
            # =====================================================
            result = data.get("result", {})

            return {
                "status": True,
                "message": "Success",
                "txn_id": data.get("txn_id"),

                # FULL RESULT
                "data": result,

                # FULL RAW RESPONSE
                "raw": data,
            }

        except requests.exceptions.RequestException as exc:

            logger.exception("REQUEST EXCEPTION OCCURRED")

            return {
                "status": False,
                "message": "API request failed",
                "error": str(exc),
            }

        except Exception as exc:

            logger.exception("UNEXPECTED EXCEPTION OCCURRED")

            return {
                "status": False,
                "message": str(exc),
            }