import requests
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)


class SurepassClient:

    def __init__(self):
        self.base_url = settings.SUREPASS_BASE_URL.rstrip("/")
        self.token = settings.SUREPASS_TOKEN

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def post(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"

        try:
            # 🔥 REQUEST LOG
            logger.info(f"[SUREPASS REQUEST] URL: {url}")
            logger.info(f"[SUREPASS REQUEST] PAYLOAD: {payload}")

            r = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=(10, 60),
            )

            # 🔥 RAW RESPONSE LOG
            logger.info(f"[SUREPASS RESPONSE] STATUS: {r.status_code}")
            logger.info(f"[SUREPASS RESPONSE] TEXT: {r.text}")

            try:
                data = r.json() if r.content else {}
            except Exception:
                logger.error("[SUREPASS ERROR] Invalid JSON response")
                data = {}

            # 🔥 FINAL PARSED LOG
            logger.info(f"[SUREPASS PARSED] {data}")

            return {
                "status_code": r.status_code,
                "data": data.get("data"),
                "message": data.get("message"),
                "success": data.get("success", False),
                "raw": data   # 👈 IMPORTANT (full response for debugging)
            }

        except requests.exceptions.Timeout:
            logger.error("[SUREPASS ERROR] Request Timeout")
            return {
                "status_code": 504,
                "message": "Request Timeout",
                "success": False
            }

        except requests.exceptions.ConnectionError:
            logger.error("[SUREPASS ERROR] Connection Error")
            return {
                "status_code": 503,
                "message": "Connection Error",
                "success": False
            }

        except Exception as e:
            logger.exception("[SUREPASS ERROR] Unexpected Error")
            return {
                "status_code": 500,
                "message": str(e),
                "success": False
            }

    # =========================
    # PREFILL
    # =========================
    def prefill_mobile(self, mobile_number):
        return self.post(
            "/prefill/prefill-by-mobile",
            {
                "mobile": mobile_number,
            },
        )

    # =========================
    # CRIF
    # =========================
    # =========================

    def crif_report_pdf(self, first_name, last_name, mobile, pan, consent="Y", raw=False):

        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "pan": pan,
            "consent": consent,
            "raw": raw,
        }

        logger.info(f"[CRIF PAYLOAD] {payload}")

        res = self.post("/credit-report-crif/fetch-report-pdf", payload)

        if not res.get("success"):
            return res

        link = (res.get("data") or {}).get("credit_report_link")

        if not link:
            return {
                "success": False,
                "message": "PDF link not found"
            }

        try:
            pdf_res = requests.get(link, timeout=60)

            if pdf_res.status_code != 200:
                return {
                    "success": False,
                    "message": "Failed to download PDF"
                }

            return {
                "success": True,
                "file": pdf_res.content   # ✅ IMPORTANT
            }

        except Exception as e:
            logger.exception("[CRIF PDF DOWNLOAD ERROR]")
            return {
                "success": False,
                "message": str(e)
            }


    # =========================
    # EQUIFAX V2
    # =========================
    def equifax_report_pdf_v2(self, name, pan, mobile, gender, consent="Y"):

        payload = {
            "name": name,
            "id_number": pan,
            "id_type": "pan",
            "mobile": mobile,
            "consent": consent,
            "gender": gender,
        }

        logger.info(f"[EQUIFAX PAYLOAD] {payload}")

        res = self.post("/credit-report-v2/fetch-pdf-report", payload)

        if not res.get("success"):
            return res

        link = (res.get("data") or {}).get("credit_report_link")

        if not link:
            return {
                "success": False,
                "message": "PDF link not found"
            }

        try:
            pdf_res = requests.get(link, timeout=60)

            if pdf_res.status_code != 200:
                return {
                    "success": False,
                    "message": "Failed to download PDF"
                }

            return {
                "success": True,
                "file": pdf_res.content
            }

        except Exception as e:
            logger.exception("[EQUIFAX PDF DOWNLOAD ERROR]")
            return {
                "success": False,
                "message": str(e)
            }
            
    # # =========================
    # # EXPERIAN
    # # =========================
    # def experian_report_pdf(self, name, mobile, pan, consent="Y"):

    #     payload = {
    #         "name": name,
    #         "mobile": mobile,
    #         "pan": pan,
    #         "consent": consent,
    #     }

    #     logger.info(f"[EXPERIAN PAYLOAD] {payload}")

    #     res = self.post("/credit-report-experian/fetch-report-pdf", payload)

    #     if not res.get("success"):
    #         return res
        
    #     if not res.get("success"):
    #             return {
    #             "success": False,
    #             "message": res.get("message"),
    #             "raw": res.get("raw")   # 🔥 full error
    #         }

    #     link = (res.get("data") or {}).get("credit_report_link")

    #     if not link:
    #         return {
    #             "success": False,
    #             "message": "PDF link not found"
    #         }

    #     try:
    #         pdf_res = requests.get(link, timeout=60)

    #         if pdf_res.status_code != 200:
    #             return {
    #                 "success": False,
    #                 "message": "Failed to download PDF"
    #             }

    #         return {
    #             "success": True,
    #             "file": pdf_res.content   # ✅ PDF binary
    #         }

    #     except Exception as e:
    #         logger.exception("[EXPERIAN PDF DOWNLOAD ERROR]")
    #         return {
    #             "success": False,
    #             "message": str(e)
    #         }
    def experian_report_pdf(self, name, mobile, pan, consent="Y"):

        payload = {
            "name": name,
            "mobile": mobile,
            "pan": pan,
            "consent": consent,
        }

        res = self.post("/credit-report-experian/fetch-report-pdf", payload)

        logger.error(f"[EXPERIAN RESPONSE] {res}")

        if not res.get("success"):
            return {
                "success": False,
                "message": res.get("message"),
                "raw": res
            }

        link = (res.get("data") or {}).get("credit_report_link")

        if not link:
            return {
                "success": False,
                "message": "PDF link not found"
            }

        # 🔥 TRY DOWNLOAD
        try:
            pdf_res = requests.get(link, timeout=20)

            if pdf_res.status_code == 200:
                return {
                    "success": True,
                    "file": pdf_res.content
                }

            else:
                # 🔥 FALLBACK: return URL
                return {
                    "success": True,
                    "pdf_url": link   # 🔥 IMPORTANT
                }

        except Exception as e:
            logger.warning(f"[PDF DOWNLOAD FAILED] {str(e)}")

            # 🔥 FALLBACK: still return URL
            return {
                "success": True,
                "pdf_url": link
            }