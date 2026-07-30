from typing import Any
import httpx

from app.core.config import settings


async def send_push(token: str, title: str, body: str, data: dict | None = None) -> bool:
    if not settings.fcm_server_key:
        return False
    payload = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": body},
            "data": data or {},
            "apns": {"payload": {"aps": {"sound": "default", "badge": 1}}},
        }
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://fcm.googleapis.com/v1/projects/vidashort/messages:send",
            headers={"Authorization": f"Bearer {settings.fcm_server_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        return resp.status_code in (200, 204)
