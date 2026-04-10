import requests
from django.conf import settings


def verify_aadhaar(aadhaar):

    url = f"{settings.SUREPASS_BASE_URL}/aadhaar-validation/aadhaar-validation"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "id_number": aadhaar
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30,
    )

    return r.json()