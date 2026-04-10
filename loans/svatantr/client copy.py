import requests
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SvatantrClient:

    def __init__(self):

        self.base_url = settings.SVATANTR_API_URL
        self.timeout = 20

    # =====================================
    # LOGIN
    # =====================================

    def login(self):

        url = f"{self.base_url}/api/user/login"

        payload = {
            "username": settings.SVATANTR_USERNAME,
            "password": settings.SVATANTR_PASSWORD,
        }

        try:

            res = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )

            res.raise_for_status()

            data = res.json()

            token = data["data"]["token"]

            telecaller_id = data["data"]["user"]["teleCallerId"]

            cache.set("svatantr_token", token, 60 * 60 * 23)
            cache.set("svatantr_telecaller_id", telecaller_id, 60 * 60 * 23)

            return token

        except Exception as e:

            logger.error(f"Svatantr login error: {e}")

            raise Exception("Svatantr login failed")

    # =====================================
    # TOKEN
    # =====================================

    def get_token(self):

        token = cache.get("svatantr_token")

        if not token:

            token = self.login()

        return token

    # =====================================
    # TELECALLER ID
    # =====================================

    def get_telecaller_id(self):

        telecaller_id = cache.get("svatantr_telecaller_id")

        if not telecaller_id:

            self.login()

            telecaller_id = cache.get("svatantr_telecaller_id")

        return telecaller_id

    # =====================================
    # HEADERS
    # =====================================

    def headers(self):

        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

    # =====================================
    # REQUEST HANDLER
    # =====================================

    def request(self, method, url, **kwargs):

        try:

            response = requests.request(
                method,
                url,
                headers=self.headers(),
                timeout=self.timeout,
                **kwargs,
            )

            # token expired

            if response.status_code == 401:

                cache.delete("svatantr_token")
                cache.delete("svatantr_telecaller_id")

                self.login()

                response = requests.request(
                    method,
                    url,
                    headers=self.headers(),
                    timeout=self.timeout,
                    **kwargs,
                )

            response.raise_for_status()

            return response.json()

        except Exception as e:

            logger.error(f"Svatantr API error: {e}")

            raise Exception("Svatantr API request failed")

    # =====================================
    # MASTER SETTINGS
    # =====================================

    def get_master_settings(self):

        url = f"{self.base_url}/api/master_data/setting"

        return self.request("GET", url)

    # =====================================
    # CATEGORIES
    # =====================================

    def get_categories(self, pincode):

        url = f"{self.base_url}/api/bank-vs-category/category"

        params = {
            "status": True,
            "pincode": pincode,
            "teleCallerId": self.get_telecaller_id(),
            "isForUTM": "Y",
        }

        return self.request("GET", url, params=params)

    # =====================================
    # USER JOURNEY
    # =====================================

    def get_journey(self, category_id):

        url = f"{self.base_url}/api/journey/user_product_jouney"

        params = {
            "categoryId": category_id,
            "teleCallerId": self.get_telecaller_id(),
        }

        return self.request("GET", url, params=params)

    # =====================================
    # BANKS
    # =====================================

    def get_banks(self, category_id, pincode):

        url = f"{self.base_url}/api/bank-vs-pincode"

        params = {
            "categoryId": category_id,
            "pinCode": pincode,
        }

        return self.request("GET", url, params=params)

    # =====================================
    # CREATE LEAD
    # =====================================

    def create_lead(self, payload):

        url = f"{self.base_url}/api/telecaller_trx/externalV2?type=Internal"

        return self.request(
            "POST",
            url,
            json=payload,
        )