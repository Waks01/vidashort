from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.models import User, AdImpression
from app.schemas.ads import AdCapResponse, AdRecordResponse


async def cap(db: AsyncSession, user_id: str) -> AdCapResponse:
    today = datetime.utcnow().date()
    result = await db.execute(select(func.count()).where(AdImpression.user_id == user_id, AdImpression.created_at >= today))
    used = result.scalar_one()
    return AdCapResponse(used=used, limit=100, remaining=max(0, 100 - used), resets_at=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat())


async def record_ad(db: AsyncSession, user_id: str, payload) -> dict:
    from app.core.errors import AppError
    if payload.watched_s < 5:
        raise AppError(status_code=400, code="watched_too_short", detail="Ad watched too short")
    existing = (await db.execute(select(AdImpression).where(AdImpression.user_id == user_id, AdImpression.ad_id == payload.ad_id))).scalar_one_or_none()
    if existing:
        raise AppError(status_code=400, code="already_recorded", detail="Ad already recorded")
    cap_info = await cap(db, user_id)
    if cap_info.remaining <= 0:
        raise AppError(status_code=429, code="cap_reached", detail="Daily ad cap reached")
    impression = AdImpression(
        id=__import__("uuid").uuid4(),
        user_id=user_id,
        ad_id=payload.ad_id,
        ad_network="appLovin",
        ad_type="rewarded",
        watched_s=payload.watched_s,
        completed=payload.completed,
        rewarded_coins=20,
    )
    db.add(impression)
    user = await db.get(User, user_id)
    if user:
        user.coins += 20
    await db.commit()
    cap_info = await cap(db, user_id)
    return AdRecordResponse(ok=True, rewarded_coins=20, new_balance=user.coins if user else 0, remaining=cap_info.remaining)