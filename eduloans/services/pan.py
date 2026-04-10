import requests
from django.conf import settings


def verify_pan(pan, name, dob):

    url = f"{settings.SUREPASS_BASE_URL}/pan/pan-verify"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "id_number": pan,
        "full_name": name,
        "dob": dob,
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30,
    )

    return r.json()