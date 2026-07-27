from typing import Any

from jose import jwt

from app.core.config import settings


async def verify_id_token(token: str) -> dict[str, Any]:
    # In production, verify against Google's certs
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"sub": payload.get("sub"), "email": payload.get("email"), "name": payload.get("name"), "picture": payload.get("picture")}
    except Exception as exc:
        raise ValueError(f"Invalid Google ID token: {exc}") from exc


async def verify_purchase(purchase_token: str, package_name: str, product_id: str) -> dict[str, Any]:
    raise NotImplementedError("Google purchase verification not implemented")