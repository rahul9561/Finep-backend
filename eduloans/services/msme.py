import requests
from django.conf import settings


def verify_msme(pan):

    url = f"{settings.SUREPASS_BASE_URL}/pan-to-msme/initialize"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "pan": pan
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=60,
    )

    return r.json()