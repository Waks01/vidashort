import json
import time
from typing import Any

import httpx
from jose import jwt

from app.core.config import settings


async def verify_id_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"sub": payload.get("sub"), "email": payload.get("email"), "name": payload.get("name"), "picture": payload.get("picture")}
    except Exception as exc:
        raise ValueError(f"Invalid Google ID token: {exc}") from exc


def _get_service_account_creds() -> dict[str, Any]:
    try:
        return json.loads(settings.google_service_account_json)
    except Exception:
        return {}


async def _get_access_token() -> str | None:
    creds = _get_service_account_creds()
    if not creds or not creds.get("client_email") or not creds.get("private_key"):
        return None

    now = int(time.time())
    claims = {
        "iss": creds["client_email"],
        "scope": "https://www.googleapis.com/auth/androidpublisher",
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600,
        "iat": now,
    }
    signed = jwt.encode(claims, creds["private_key"], algorithm="RS256")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": signed,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
    except Exception:
        return None


async def verify_purchase(purchase_token: str, package_name: str, product_id: str) -> dict[str, Any]:
    access_token = await _get_access_token()
    if not access_token:
        return {"valid": False}

    url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/"
        f"applications/{package_name}/purchases/products/{product_id}/tokens/{purchase_token}"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return {"valid": False}

    expiry = data.get("expiryTimeMillis") or data.get("expiryDateMillis") or ""
    return {
        "valid": True,
        "product_id": product_id,
        "purchase_token": purchase_token,
        "expires_at": expiry,
    }