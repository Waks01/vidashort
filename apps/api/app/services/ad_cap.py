from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AdImpression
from app.db.session import get_redis
from app.services.revenue_split import DAILY_AD_CAP


_r: Redis | None = None


def _get_redis() -> Redis:
    global _r
    if _r is None:
        _r = get_redis()
    return _r


def _today_key(user_id: str) -> str:
    return f"adcap:{user_id}:{datetime.now(timezone.utc).date().isoformat()}"


def _ad_key(user_id: str, ad_id: str) -> str:
    return f"adseen:{user_id}:{ad_id}"


async def _used_today(db: AsyncSession, user_id: str) -> int:
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(func.count()).where(
            AdImpression.user_id == user_id,
            AdImpression.created_at >= today,
        )
    )
    return int(result.scalar_one())


async def remaining(db: AsyncSession, user_id: str) -> int:
    r = _get_redis()
    redis_used = int(await r.get(_today_key(user_id)) or 0)
    db_used = await _used_today(db, user_id)
    used = max(redis_used, db_used)
    if used >= DAILY_AD_CAP:
        return 0
    return DAILY_AD_CAP - used


async def record_ad(db: AsyncSession, user_id: str, ad_id: str) -> None:
    r = _get_redis()
    today = _today_key(user_id)
    pipe = r.pipeline()
    pipe.incr(today)
    pipe.expire(today, 86400)
    await pipe.execute()
    await r.set(_ad_key(user_id, ad_id), "1", ex=86400)
    impression = AdImpression(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        ad_id=ad_id,
        ad_network="appLovin",
        ad_type="rewarded",
        watched_s=15,
        completed=True,
        rewarded_coins=0,
    )
    db.add(impression)
    await db.commit()


async def cap_info(db: AsyncSession, user_id: str) -> dict:
    r = _get_redis()
    key = _today_key(user_id)
    redis_used = int(await r.get(key) or 0)
    db_used = await _used_today(db, user_id)
    used = max(redis_used, db_used)
    return {
        "used": used,
        "limit": DAILY_AD_CAP,
        "remaining": max(0, DAILY_AD_CAP - used),
        "resets_at": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
    }
