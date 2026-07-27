from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Series, Episode, Favorite
from app.schemas.content import (
    FeaturedResponse,
    FavoriteResponse,
    PaywallDecisionSchema,
    SeriesDetail,
    SeriesItem,
    SeriesListResponse,
    StreamResponse,
)


async def list_series(db: AsyncSession, cursor, limit, category, source, q, language):
    query = select(Series).where(Series.is_published == True)
    if category:
        query = query.where(Series.category == category)
    if source:
        query = query.where(Series.source == source)
    if language:
        query = query.where(Series.language == language)
    if q:
        query = query.where(Series.title.ilike(f"%{q}%"))
    query = query.order_by(Series.total_episodes.desc(), Series.created_at.desc()).limit(limit)
    result = await db.execute(query)
    series = result.scalars().all()
    items = [
        SeriesItem(
            id=str(s.id),
            slug=s.slug,
            title=s.title,
            synopsis=s.synopsis,
            cover_url=s.cover_url,
            backdrop_url=s.backdrop_url,
            category=s.category,
            language=s.language,
            source=s.source,
            creator_id=str(s.creator_id) if s.creator_id else None,
            tags=s.tags_list,
            total_episodes=s.total_episodes,
            free_episodes=s.free_episodes,
            is_vip_only=s.is_vip_only,
            rating=float(s.rating),
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in series
    ]
    return SeriesListResponse(items=items, next_cursor=None)


async def get_series(db: AsyncSession, slug: str) -> SeriesDetail:
    result = await db.execute(select(Series).where(Series.slug == slug))
    series = result.scalar_one_or_none()
    if not series:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    eps_result = await db.execute(select(Episode).where(Episode.series_id == series.id).order_by(Episode.number))
    episodes = [
        {
            "number": e.number,
            "title": e.title,
            "synopsis": e.synopsis,
            "duration_s": e.duration_s,
            "required_coins": e.required_coins,
            "is_free": e.is_free,
            "thumbnail_url": e.thumbnail_url,
        }
        for e in eps_result.scalars().all()
    ]
    return SeriesDetail(
        series=SeriesItem(
            id=str(series.id),
            slug=series.slug,
            title=series.title,
            synopsis=series.synopsis,
            cover_url=series.cover_url,
            backdrop_url=series.backdrop_url,
            category=series.category,
            language=series.language,
            source=series.source,
            creator_id=str(series.creator_id) if series.creator_id else None,
            tags=series.tags_list,
            total_episodes=series.total_episodes,
            free_episodes=series.free_episodes,
            is_vip_only=series.is_vip_only,
            rating=float(series.rating),
            created_at=series.created_at.isoformat() if series.created_at else None,
        ),
        episodes=episodes,
    )


async def stream_episode(db: AsyncSession, user_id: str, slug: str, n: int) -> StreamResponse:
    from app.services.paywall import decide, pay_with_coins
    from app.integrations.cloudflare_stream import mint_signed_playback_url
    series = (await db.execute(select(Series).where(Series.slug == slug))).scalar_one_or_none()
    if not series:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    episode = (await db.execute(select(Episode).where(Episode.series_id == series.id, Episode.number == n))).scalar_one_or_none()
    if not episode:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="Episode not found")
    decision = await decide(db, user_id, episode.id)
    if not decision.get("allowed"):
        from app.core.errors import PaywallRequired
        raise PaywallRequired(detail="Entitlement required")
    playback_url = await mint_signed_playback_url(episode.video_uid)
    return StreamResponse(
        episode_id=str(episode.id),
        playback_url=playback_url,
        expires_at="",
        captions_url=None,
        preroll_ad=None,
        midroll_at_s=episode.ad_midroll_at_s,
        poster_url=episode.thumbnail_url,
    )


async def favorite(db: AsyncSession, user_id: str, series_id: str):
    fav = Favorite(user_id=user_id, series_id=series_id)
    db.add(fav)
    await db.commit()


async def unfavorite(db: AsyncSession, user_id: str, series_id: str):
    result = await db.execute(select(Favorite).where(Favorite.user_id == user_id, Favorite.series_id == series_id))
    fav = result.scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.commit()


async def featured(db: AsyncSession) -> FeaturedResponse:
    return FeaturedResponse(items=[])