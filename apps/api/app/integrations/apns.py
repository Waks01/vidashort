from typing import Any
import httpx

from app.core.config import settings


async def send_push(token: str, title: str, body: str, data: dict | None = None) -> bool:
    if not settings.apns_key_id:
        return False
    payload = {"aps": {"alert": {"title": title, "body": body}, "sound": "default", "badge": 1}, "data": data or {}}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.push.apple.com/3/device/{token}",
            headers={"Authorization": f"Bearer {settings.apns_auth_token}", "apns-topic": settings.apple_bundle_id, "apns-push-type": "alert"},
            json=payload,
            timeout=10,
        )
        return resp.status_code in (200, 204)
