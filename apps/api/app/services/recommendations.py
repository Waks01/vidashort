from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Series, WatchHistory, User


async def for_user(db: AsyncSession, user_id: str, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(Series)
        .join(WatchHistory, WatchHistory.episode_id == Series.id)
        .where(WatchHistory.user_id == user_id)
        .order_by(WatchHistory.watched_at.desc())
        .limit(limit)
    )
    return [{"id": str(s.id), "title": s.title, "cover_url": s.cover_url} for s in result.scalars().all()]


async def trending(db: AsyncSession, limit: int = 10) -> list[dict]:
    result = await db.execute(select(Series).where(Series.is_published == True).order_by(Series.total_episodes.desc()).limit(limit))
    return [{"id": str(s.id), "title": s.title, "cover_url": s.cover_url} for s in result.scalars().all()]