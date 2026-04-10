import requests
from django.conf import settings

BASE_URL = settings.SUREPASS_BASE_URL


def create_client(name, mobile):

    url = f"{BASE_URL}/client"

    headers = {
        "Authorization": f"Bearer {settings.SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "name": name,
        "mobile": mobile,
        "consent": "Y"
    }

    res = requests.post(url, headers=headers, json=payload)

    return res.json()


def upload_statement(client_id, file):

    url = f"{BASE_URL}/upload"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
    }

    data = {
        "client_id": client_id,
    }

    files = {
        "file": file,
    }

    res = requests.post(
        url,
        headers=headers,
        data=data,
        files=files,
    )

    return res.json()