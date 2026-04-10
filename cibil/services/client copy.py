#service/client.py
import requests
import logging
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)
class BureauAPIException(Exception):
    pass


class BureauClient:


    # @staticmethod
    # def fetch_prefill(mobile: str,first_name):

    #     url = f"{settings.CIBIL_BASE_URL}/prefill"

    #     headers = {
    #         "Token": settings.CIBIL_TOKEN,
    #         "API-KEY": settings.CIBIL_API_KEY,
    #     }

    #     payload = {
    #         "mobile": str(mobile).strip(),
    #         "first_name": first_name
    #     }
    #     print("payload:",payload )

    #     session = BureauClient._get_session()

    #     try:
    #         response = session.post(
    #             url=url,
    #             data=payload,
    #             headers=headers,
    #             timeout=settings.CIBIL_TIMEOUT
    #         )

    #         response.raise_for_status()

    #     except requests.Timeout:
    #         logger.error("PREFILL Timeout")
    #         raise BureauAPIException("Prefill service timeout")

    #     except requests.HTTPError:
    #         logger.error(response.text)
    #         raise BureauAPIException("Prefill API returned error")

    #     except requests.RequestException as e:
    #         logger.error(str(e))
    #         raise BureauAPIException("Prefill service unavailable")

    #     try:
    #         json_data = response.json()

    #         logger.info(f"PREFILL RESPONSE: {json_data}")

    #         if not json_data.get("status"):
    #             return {
    #                 "success": False,
    #                 "message": json_data.get("message", "Prefill failed")
    #             }

    #         # return {
    #         #     "success": True,
    #         #     "data": json_data.get("data", {})
                
    #         # }
    #         data = json_data.get("data", {})

    #         pan_list = data.get("pan_number", [])
    #         pan = pan_list[0] if pan_list else None

    #         return {
    #             "success": True,
    #             "data": {
    #                 "name": data.get("full_name"),
    #                 "pan": pan
    #             }
    #         }

    #     except ValueError:
    #         raise BureauAPIException("Invalid JSON response")

    @staticmethod
    def _get_session():
        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        return session

    @staticmethod
    def generate_report(report_type: str, payload: dict):

        url = f"{settings.CIBIL_BASE_URL}/generate-report"

        headers = {
            "Token": settings.CIBIL_TOKEN,
            "API-KEY": settings.CIBIL_API_KEY,
        }

        session = BureauClient._get_session()

        try:
            response = session.post(
                url=url,
                data=payload,
                headers=headers,
                timeout=settings.CIBIL_TIMEOUT
            )

            response.raise_for_status()
            logger.info(f"{report_type.upper()} Success - {response.status_code}")

        except requests.Timeout:
            logger.error(f"{report_type.upper()} Timeout")
            raise BureauAPIException("Service timeout")

        # except requests.HTTPError:
        #     logger.error(response.text)
        #     raise BureauAPIException("API returned error response")
        except requests.HTTPError as e:
            try:
                error_json = response.json()
                message = error_json.get("message", "API returned error")
            except Exception:
                message = response.text

            logger.error(f"{report_type} API ERROR: {message}")

            raise BureauAPIException(message)
        # new

        except requests.RequestException as e:
            logger.error(str(e))
            raise BureauAPIException("Service unavailable")

        try:
            json_data = response.json()
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

            # 🔽 Download PDF from report_url
            pdf_response = session.get(report_url)

            if pdf_response.status_code != 200:
                return {
                    "success": False,
                    "message": "Failed to download report"
                }

            return {
                "success": True,
                "file": pdf_response.content
            }

        except ValueError:
            raise BureauAPIException("Invalid JSON response")
