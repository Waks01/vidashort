from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

import hashlib

from app.core.config import settings
from app.core.errors import AppError
from app.db.session import get_db, get_redis
from app.integrations import cloudflare_stream as cloudflare, revenuecat, apple, google
from app.services import webhooks as webhook_service

router = APIRouter()


async def _webhook_idempotency(provider: str, body: bytes) -> bool:
    body_hash = hashlib.sha256(body).hexdigest()
    r = get_redis()
    key = f"webhook:idempotency:{provider}:{body_hash}"
    if await r.exists(key):
        return True
    await r.set(key, "1", ex=86400)
    return False


@router.post("/cloudflare", status_code=status.HTTP_202_ACCEPTED)
async def cloudflare_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not webhook_service.verify_signature(settings.cf_webhook_secret, body, request.headers.get("X-Vidashort-Signature", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    if await _webhook_idempotency("cloudflare", body):
        return {"ok": True, "duplicate": True}
    payload = await request.json()
    await webhook_service.handle_cloudflare(db, payload)
    return {"ok": True}


@router.post("/revenuecat", status_code=status.HTTP_202_ACCEPTED)
async def revenuecat_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not webhook_service.verify_signature(settings.revenuecat_webhook_secret, body, request.headers.get("X-Vidashort-Signature", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    if await _webhook_idempotency("revenuecat", body):
        return {"ok": True, "duplicate": True}
    payload = await request.json()
    await webhook_service.handle_revenuecat(db, payload)
    return {"ok": True}


@router.post("/apple", status_code=status.HTTP_202_ACCEPTED)
async def apple_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not webhook_service.verify_signature(settings.apple_private_key, body, request.headers.get("X-Vidashort-Signature", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    if await _webhook_idempotency("apple", body):
        return {"ok": True, "duplicate": True}
    payload = await request.json()
    await webhook_service.handle_apple(db, payload)
    return {"ok": True}


@router.post("/google", status_code=status.HTTP_202_ACCEPTED)
async def google_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not webhook_service.verify_signature(settings.google_service_account_json, body, request.headers.get("X-Vidashort-Signature", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    if await _webhook_idempotency("google", body):
        return {"ok": True, "duplicate": True}
    payload = await request.json()
    await webhook_service.handle_google(db, payload)
    return {"ok": True}