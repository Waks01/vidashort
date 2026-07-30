import json
from typing import Any

import httpx
from jose import jwt

from app.core.config import settings


async def verify_identity_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"sub": payload.get("sub"), "email": payload.get("email"), "email_verified": payload.get("email_verified")}
    except Exception as exc:
        raise ValueError(f"Invalid Apple identity token: {exc}") from exc


async def verify_receipt(receipt_data: str) -> dict[str, Any]:
    prod_url = "https://buy.itunes.apple.com/verifyReceipt"
    sandbox_url = "https://sandbox.itunes.apple.com/verifyReceipt"
    payload = {
        "receipt-data": receipt_data,
        "password": settings.apple_shared_secret,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(prod_url, json=payload, timeout=15)
            data = resp.json()
    except Exception:
        return {"valid": False}

    status = data.get("status")
    if status == 21007:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(sandbox_url, json=payload, timeout=15)
                data = resp.json()
                status = data.get("status", status)
        except Exception:
            return {"valid": False}

    if status != 0:
        return {"valid": False}

    latest = data.get("latest_receipt_info") or data.get("receipt", {}).get("in_app", [])
    product_id = ""
    original_txn_id = ""
    expires_at = ""
    if latest:
        first = latest[0] if isinstance(latest, list) else latest
        product_id = first.get("product_id", "")
        original_txn_id = first.get("original_transaction_id", "")
        expires_at = first.get("expires_date_ms", "")

    return {
        "valid": True,
        "product_id": product_id,
        "original_txn_id": original_txn_id,
        "expires_at": expires_at,
    }