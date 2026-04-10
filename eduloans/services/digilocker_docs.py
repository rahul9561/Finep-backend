import requests
from django.conf import settings


def verify_digilocker_account(id_number):

    url = f"{settings.SUREPASS_BASE_URL}/digilocker/verify-account"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "id_number": id_number
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        verify=False,
        timeout=30,
    )

    try:
        return r.json()
    except:
        return {"success": False}


def verify_education_2017(docs):

    has_10 = False
    has_12 = False
    has_grad = False

    for d in docs:

        name = str(d.get("name", "")).lower()
        year = int(d.get("year", 0) or 0)

        if year < 2017:
            continue

        if "10" in name:
            has_10 = True

        if "12" in name:
            has_12 = True

        if "degree" in name or "graduation" in name:
            has_grad = True

    return {
        "10th": has_10,
        "12th": has_12,
        "graduation": has_grad,
        "valid": has_10 and has_12 and has_grad,
    }