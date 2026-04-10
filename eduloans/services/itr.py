import requests
from django.conf import settings


def verify_itr(pan):

    url = f"{settings.SUREPASS_BASE_URL}/itr/itr"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "pan": pan,
        "consent": "Y"
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=60,
    )

    return r.json()