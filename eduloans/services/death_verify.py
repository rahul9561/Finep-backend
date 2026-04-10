import requests
from django.conf import settings



URL = f"{settings.SUREPASS_BASE_URL}/death/verification"


def verify_death(serial_number, state_name):

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "serial_number": serial_number,
        "state_name": state_name,
    }

    r = requests.post(
        URL,
        json=payload,
        headers=headers,
        verify=False,
        timeout=30,
    )

    try:
        return r.json()
    except:
        return {"success": False}