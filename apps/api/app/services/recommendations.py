from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.models import Series, WatchHistory, Favorite


async def for_user(db: AsyncSession, user_id: str, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(Series)
        .join(WatchHistory, WatchHistory.episode_id == Series.id)
        .where(WatchHistory.user_id == user_id)
        .order_by(desc(WatchHistory.watched_at))
        .limit(limit)
    )
    return [{"id": str(s.id), "title": s.title, "cover_url": s.cover_url, "category": s.category} for s in result.scalars().all()]


async def trending(db: AsyncSession, limit: int = 20) -> list[dict]:
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(Series, func.count(WatchHistory.user_id).label("views"))
        .join(WatchHistory, WatchHistory.episode_id == Series.id)
        .where(WatchHistory.watched_at >= week_ago, Series.is_published == True)
        .group_by(Series.id)
        .order_by(desc("views"))
        .limit(limit)
    )
    return [{"id": str(s.id), "title": s.title, "cover_url": s.cover_url, "category": s.category, "views": int(views)} for s, views in result.all()]


async def new_series(db: AsyncSession, limit: int = 20) -> list[dict]:
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(Series)
        .where(Series.created_at >= week_ago, Series.is_published == True)
        .order_by(desc(Series.created_at))
        .limit(limit)
    )
    return [{"id": str(s.id), "title": s.title, "cover_url": s.cover_url, "category": s.category} for s in result.scalars().all()]


async def popular_by_genre(db: AsyncSession, genre: str, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(Series)
        .where(Series.category == genre, Series.is_published == True)
        .order_by(desc(Series.rating))
        .limit(limit)
    )
    return [{"id": str(s.id), "title": s.title, "cover_url": s.cover_url, "category": s.category} for s in result.scalars().all()]