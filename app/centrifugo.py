import time
import jwt
import requests
from django.conf import settings


def make_centrifugo_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": int(time.time()) + 3600}
    return jwt.encode(payload, settings.CENTRIFUGO_TOKEN_SECRET, algorithm="HS256")


def centrifugo_publish(channel: str, data: dict) -> None:
    headers = {"Authorization": f"apikey {settings.CENTRIFUGO_API_KEY}"}
    body = {"method": "publish", "params": {"channel": channel, "data": data}}
    r = requests.post(settings.CENTRIFUGO_API_URL, json=body, headers=headers, timeout=3)
    r.raise_for_status()
