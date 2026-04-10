import requests
from django.conf import settings


def verify_gst(gst):

    url = f"{settings.SUREPASS_BASE_URL}/corporate/gstin"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "id_number": gst
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=60,
    )

    return r.json()