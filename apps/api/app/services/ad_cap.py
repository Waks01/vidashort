"""Daily ad-cap service.

Per CLAUDE.md §4 the cap is locked at 100 impressions per user per UTC day.
The counter lives in Postgres (`AdImpression.created_at`) so it's accurate
even when Redis is down. Redis could be added later for hot-path caching,
but the source of truth is the DB row count.

This module is the only place that knows the magic number 100 — every caller
must go through `remaining()` / `record_ad()` / `cap_info()` so the lock is
enforced in one place.
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdImpression
from app.services.revenue_split import DAILY_AD_CAP


async def remaining(db: AsyncSession, user_id: str) -> int:
    """How many rewarded ads the user can still watch today (UTC day)."""
    return max(0, DAILY_AD_CAP - await _used_today(db, user_id))


async def _used_today(db: AsyncSession, user_id: str) -> int:
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count()).where(AdImpression.user_id == user_id, AdImpression.created_at >= today)
    )
    return int(result.scalar_one())


def _resets_at_iso() -> str:
    """ISO 8601 string for the next UTC midnight (when the cap resets)."""
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


async def cap_info(db: AsyncSession, user_id: str) -> dict:
    """Return the {used, limit, remaining, resets_at} dict that the /v1/ads/cap
    route serializes. `used` is the count from midnight UTC; `remaining` is
    DAILY_AD_CAP - used, clamped at 0; `resets_at` is the ISO timestamp of
    the next midnight UTC.
    """
    used = await _used_today(db, user_id)
    return {
        "used": used,
        "limit": DAILY_AD_CAP,
        "remaining": max(0, DAILY_AD_CAP - used),
        "resets_at": _resets_at_iso(),
    }