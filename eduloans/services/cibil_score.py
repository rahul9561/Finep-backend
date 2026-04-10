import requests
from django.conf import settings


def fetch_cibil_score(pan, mobile, name, gender):

    url = f"{settings.SUREPASS_BASE_URL}/credit-report-cibil/score"
    # url="https://sandbox.surepass.app/api/v1/credit-report-cibil/score"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "pan": pan,
        "mobile": mobile,
        "name": name,
        "consent": "Y",
        "gender": gender,
    }

    r = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=60,
    )

    data = r.json()

    print("SUREPASS RESPONSE", data)

    if not data.get("success"):
        return None, data

    # ✅ FIX HERE
    score = data.get("data", {}).get("credit_score")

    return score, data