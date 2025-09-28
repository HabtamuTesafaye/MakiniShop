# utils/chapa.py
import requests
import os

CHAPA_SECRET_KEY = os.environ.get("CHAPA_SECRET_KEY", "")
CHAPA_BASE_URL = "https://api.chapa.co/v1/transaction/initialize"

def create_chapa_payment(email: str, amount: float, tx_ref: str, callback_url: str):
    payload = {
        "email": email,
        "amount": amount,
        "tx_ref": tx_ref,
        "currency": "ETB",
        "callback_url": callback_url
    }
    headers = {
        "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(CHAPA_BASE_URL, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()
