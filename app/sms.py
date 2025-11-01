import requests

GATEWAY_URL = "http://127.0.0.1:8080/send-sms"

def send_sms(to: str, message: str):
    try:
        res = requests.post(GATEWAY_URL, json={"phone": to, "message": message}, timeout=5)
        return res.status_code
    except Exception as e:
        return str(e)
