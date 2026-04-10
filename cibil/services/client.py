import requests
import logging
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class BureauAPIException(Exception):
    pass


class BureauClient:

    # ============================
    # SESSION
    # ============================

    @staticmethod
    def _get_session():

        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry)

        session.mount("https://", adapter)

        return session


    
    @staticmethod
    def fetch_prefill(mobile: str, first_name: str):

        url = f"{settings.CIBIL_BASE_URL}/prefill"

        headers = {
            "Token": settings.CIBIL_TOKEN,
            "API-KEY": settings.CIBIL_API_KEY,
        }

        payload = {
            "mobile": str(mobile).strip(),
            "first_name": first_name
        }

        session = BureauClient._get_session()

        response = session.post(
            url=url,
            data=payload,
            headers=headers,
            timeout=settings.CIBIL_TIMEOUT
        )

        json_data = response.json()

        logger.info(f"PREFILL RESPONSE: {json_data}")

        return json_data   # ✅ FULL RESPONSE RETURN


    # ============================
    # GENERATE REPORT
    # ============================

    @staticmethod
    def generate_report(report_type: str, payload: dict):

        url = f"{settings.CIBIL_BASE_URL}/generate-report"

        headers = {
            "Token": settings.CIBIL_TOKEN,
            "API-KEY": settings.CIBIL_API_KEY,
        }

        session = BureauClient._get_session()

        try:

            logger.info(f"{report_type} PAYLOAD: {payload}")

            response = session.post(
                url=url,
                data=payload,
                headers=headers,
                timeout=settings.CIBIL_TIMEOUT
            )

            response.raise_for_status()

        except requests.Timeout:

            logger.error(f"{report_type} timeout")

            raise BureauAPIException("Service timeout")

        except requests.HTTPError:

            try:

                error_json = response.json()

                message = error_json.get("message")

            except Exception:

                message = response.text

            logger.error(f"{report_type} API ERROR: {message}")

            raise BureauAPIException(message)

        except requests.RequestException as e:

            logger.error(str(e))

            raise BureauAPIException("Service unavailable")

        # --------------------
        # JSON RESPONSE
        # --------------------

        try:

            json_data = response.json()

        except Exception:

            raise BureauAPIException("Invalid JSON response")

        logger.info(f"VERIFYAL RESPONSE: {json_data}")

        if json_data.get("status") != 200:

            return {
                "success": False,
                "message": json_data.get("message", "API error")
            }

        report_url = json_data.get("data", {}).get("report_url")

        if not report_url:

            return {
                "success": False,
                "message": "Report URL not found"
            }

        # --------------------
        # DOWNLOAD PDF
        # --------------------

        try:

            pdf_response = session.get(report_url)

        except Exception:

            raise BureauAPIException("Report download failed")

        if pdf_response.status_code != 200:

            return {
                "success": False,
                "message": "Failed to download report"
            }

        return {
            "success": True,
            "file": pdf_response.content
        }