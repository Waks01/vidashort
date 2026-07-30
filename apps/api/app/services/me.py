from datetime import datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import User, WatchHistory, AdImpression
from app.schemas.user import MeResponse


async def get_me(db: AsyncSession, user_id: str) -> MeResponse:
    user = await db.get(User, user_id)
    if not user:
        raise AppError(status_code=404, code="not_found", detail="User not found")
    ad_cap_used = (await db.execute(select(func.count()).where(AdImpression.user_id == user_id, AdImpression.created_at >= datetime.utcnow().date()))).scalar_one()
    return MeResponse(
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "avatarUrl": user.avatar_url,
            "genres": user.genres_list,
            "language": user.language,
            "ageConfirmed": user.age_confirmed,
            "onboarded": user.onboarded,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        },
        wallet={"coins": user.coins, "vip": {"active": False, "until": None}},
        adCap={"used": ad_cap_used, "limit": 100, "remaining": max(0, 100 - ad_cap_used), "resetsAt": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()},
        streak={"day": 0, "lastClaimedOn": None},
    )


async def update_me(db: AsyncSession, user_id: str, payload) -> MeResponse:
    user = await db.get(User, user_id)
    if not user:
        raise AppError(status_code=404, code="not_found", detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.genres is not None:
        user.genres_list = payload.genres
    if payload.language is not None:
        user.language = payload.language
    await db.commit()
    await db.refresh(user)
    return await get_me(db, user_id)


async def age_confirm(db: AsyncSession, user_id: str, confirmed: bool):
    user = await db.get(User, user_id)
    if not user:
        raise AppError(status_code=404, code="not_found", detail="User not found")
    user.age_confirmed = confirmed
    await db.commit()


async def delete_me(db: AsyncSession, user_id: str):
    user = await db.get(User, user_id)
    if not user:
        raise AppError(status_code=404, code="not_found", detail="User not found")
    user.deleted_at = datetime.utcnow()
    user.email = f"deleted-{user_id}@deleted.vidashort"
    user.name = "Deleted user"
    user.avatar_url = None
    await db.commit()


async def watch_history(db: AsyncSession, user_id: str) -> list[dict]:
    from app.db.models import WatchHistory as WatchHistoryModel
    result = await db.execute(
        select(WatchHistoryModel).where(WatchHistoryModel.user_id == user_id).order_by(WatchHistoryModel.watched_at.desc()).limit(50)
    )
    items = []
    for h in result.scalars().all():
        items.append({
            "id": str(h.id),
            "seriesId": str(h.episode.series_id) if h.episode else None,
            "episodeId": str(h.episode_id),
            "position_s": h.position_s,
            "completed": h.completed,
            "watchedAt": h.watched_at.isoformat() if h.watched_at else None,
        })
    return items


async def favorites(db: AsyncSession, user_id: str) -> dict:
    from app.db.models import Favorite as FavoriteModel
    result = await db.execute(
        select(FavoriteModel).where(FavoriteModel.user_id == user_id).order_by(FavoriteModel.created_at.desc())
    )
    items = [{"seriesId": str(f.series_id), "createdAt": f.created_at.isoformat() if f.created_at else None} for f in result.scalars().all()]
    return {"items": items}