from typing import Any

import httpx

from app.core.config import settings


async def fetch_subscriber_info(app_user_id: str) -> dict[str, Any] | None:
    if not settings.revenuecat_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.revenuecat.com/v1/subscribers/{app_user_id}",
            headers={"Authorization": f"Bearer {settings.revenuecat_api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("subscriber")