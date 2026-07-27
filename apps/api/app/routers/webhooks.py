from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.db.session import get_db
from app.integrations import cloudflare_stream as cloudflare, revenuecat, apple, google
from app.services import webhooks as webhook_service

router = APIRouter()


@router.post("/cloudflare", status_code=status.HTTP_202_ACCEPTED)
async def cloudflare_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not webhook_service.verify_signature(settings.cf_stream_signing_key, body, request.headers.get("X-Vidashort-Signature", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
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
    payload = await request.json()
    await webhook_service.handle_google(db, payload)
    return {"ok": True}