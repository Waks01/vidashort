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


async def list_comments(db: AsyncSession, episode_id: str, cursor: str | None, limit: int, order: str = "new") -> dict:
    from app.db.models import Comment as CommentModel, User
    stmt = select(CommentModel, User).where(CommentModel.episode_id == episode_id, CommentModel.deleted_at == None, CommentModel.parent_id == None).join(User, CommentModel.user_id == User.id, isouter=True)
    if order == "top":
        stmt = stmt.order_by(CommentModel.likes.desc())
    else:
        stmt = stmt.order_by(CommentModel.created_at.desc())
    stmt = stmt.limit(limit)
    if cursor:
        stmt = stmt.where(CommentModel.id > cursor)
    result = await db.execute(stmt)
    rows = result.all()
    items = []
    for c, u in rows:
        items.append({
            "id": str(c.id),
            "user": {"id": str(c.user_id), "name": u.name if u else "Deleted user", "avatarUrl": u.avatar_url if u else None},
            "body": c.body,
            "likes": c.likes,
            "liked": False,
            "replies": [],
            "createdAt": c.created_at.isoformat() if c.created_at else None,
        })
    next_cursor = rows[-1][0].id if len(rows) == limit else None
    return {"items": items, "next_cursor": next_cursor}


async def create_comment(db: AsyncSession, user_id: str, episode_id: str, body: str, parent_id: str | None = None) -> dict:
    from app.core.errors import AppError
    from app.db.models import Comment as CommentModel
    comment = CommentModel(
        id=str(__import__("uuid").uuid4()),
        episode_id=episode_id,
        user_id=user_id,
        body=body,
        likes=0,
        parent_id=parent_id,
    )
    db.add(comment)
    await db.commit()
    return {"id": str(comment.id), "body": comment.body, "parent_id": str(comment.parent_id) if comment.parent_id else None, "createdAt": comment.created_at.isoformat() if comment.created_at else None}


async def like_comment(db: AsyncSession, user_id: str, comment_id: str) -> dict:
    from app.core.errors import AppError
    from app.db.models import Comment as CommentModel
    comment = await db.get(CommentModel, comment_id)
    if not comment:
        raise AppError(status_code=404, code="not_found", detail="Comment not found")
    comment.likes += 1
    await db.commit()
    return {"likes": comment.likes}


async def list_replies(db: AsyncSession, parent_id: str, limit: int = 20) -> dict:
    from app.db.models import Comment as CommentModel, User
    stmt = select(CommentModel, User).where(CommentModel.parent_id == parent_id, CommentModel.deleted_at == None).join(User, CommentModel.user_id == User.id, isouter=True).order_by(CommentModel.created_at.asc()).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()
    items = []
    for r, u in rows:
        items.append({
            "id": str(r.id),
            "user": {"id": str(r.user_id), "name": u.name if u else "Deleted user", "avatarUrl": u.avatar_url if u else None},
            "body": r.body,
            "likes": r.likes,
            "liked": False,
            "replies": [],
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        })
    return {"items": items}