from typing import Any

from jose import jwt

from app.core.config import settings


async def verify_identity_token(token: str) -> dict[str, Any]:
    # In production, verify against Apple's JWKS
    # For now, decode without verification (dev only)
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"sub": payload.get("sub"), "email": payload.get("email"), "email_verified": payload.get("email_verified")}
    except Exception as exc:
        raise ValueError(f"Invalid Apple identity token: {exc}") from exc


async def verify_receipt(receipt_data: str) -> dict[str, Any]:
    # In production, verify against App Store Server API
    raise NotImplementedError("Apple receipt verification not implemented")