import requests
import logging

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


class SvatantrClient:

    def __init__(self):

        self.base_url = settings.SVATANTR_API_URL
        self.timeout = 20

    # =========================
    # LOGIN
    # =========================

    def login(self):

        url = f"{self.base_url}/api/user/login"

        payload = {
            "username": settings.SVATANTR_USERNAME,
            "password": settings.SVATANTR_PASSWORD,
        }

        res = requests.post(
            url,
            json=payload,
            timeout=self.timeout,
        )

        res.raise_for_status()

        data = res.json()

        token = data["data"]["token"]
        telecaller_id = data["data"]["user"]["teleCallerId"]

        cache.set("sv_token", token, 60 * 60 * 23)
        cache.set("sv_telecaller", telecaller_id, 60 * 60 * 23)

        return token

    # =========================
    # TOKEN
    # =========================

    def get_token(self):

        token = cache.get("sv_token")

        if not token:
            token = self.login()

        return token

    # =========================
    # TELECALLER
    # =========================

    def get_telecaller_id(self):

        tid = cache.get("sv_telecaller")

        if not tid:
            self.login()
            tid = cache.get("sv_telecaller")

        return tid

    # =========================
    # HEADERS
    # =========================

    def headers(self):

        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

    # =========================
    # REQUEST
    # =========================

    def request(self, method, url, **kwargs):

        res = requests.request(
            method,
            url,
            headers=self.headers(),
            timeout=self.timeout,
            **kwargs,
        )

        if res.status_code == 401:

            cache.delete("sv_token")
            cache.delete("sv_telecaller")

            self.login()

            res = requests.request(
                method,
                url,
                headers=self.headers(),
                timeout=self.timeout,
                **kwargs,
            )

        res.raise_for_status()

        return res.json()

    # =========================
    # MASTER SETTINGS
    # =========================

    def get_master_settings(self):

        url = f"{self.base_url}/api/master_data/setting"

        return self.request("GET", url)

    # =========================
    # CATEGORY
    # =========================

    def get_categories(self, pincode):

        url = f"{self.base_url}/api/bank-vs-category/category"

        params = {
            "status": True,
            "pincode": pincode,
            "teleCallerId": self.get_telecaller_id(),
            "isForUTM": "Y",
        }

        return self.request("GET", url, params=params)

    # =========================
    # JOURNEY
    # =========================

    def get_journey(self, category_id):

        url = f"{self.base_url}/api/journey/user_product_jouney"

        params = {
            "categoryId": category_id,
            "teleCallerId": self.get_telecaller_id(),
        }

        return self.request("GET", url, params=params)

    # =========================
    # BANKS
    # =========================

    def get_banks(self, category_id, pincode):

        url = f"{self.base_url}/api/bank-vs-pincode"

        params = {
            "categoryId": category_id,
            "pinCode": pincode,
        }

        return self.request("GET", url, params=params)

    # =========================
    # CREATE LEAD
    # =========================

    def create_lead(self, payload):

        url = f"{self.base_url}/api/telecaller_trx/externalV2?type=Internal"

        return self.request(
            "POST",
            url,
            json=payload,
        )
        
        # =========================
    # MIS DATA
    # =========================

    def get_mis(self, skip=0, limit=20, start=None, end=None, status=None):

            url = f"{self.base_url}/api/executive"

            params = {
                "skip": skip,
                "limit": limit,
                "teleCallerId": self.get_telecaller_id(),
            }

            if start:
                params["startDate"] = start

            if end:
                params["endDate"] = end

            if status:
                params["executiveStatus"] = status

            return self.request(
                "GET",
                url,
                params=params,
            )