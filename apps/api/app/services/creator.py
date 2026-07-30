from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Series, CreatorEarning, PayoutRequest
from app.schemas.creator import (
    CreatorAnalyticsResponse,
    CreatorEarningsResponse,
    CreatorProfileRequest,
    CreatorProfileResponse,
    CreatorSeriesCreateRequest,
    CreatorSeriesCreateResponse,
    CreatorSeriesResponse,
    PayoutListResponse,
    PayoutRequest as PayoutRequestSchema,
    PayoutResponse,
)


async def profile(db: AsyncSession, user_id: str) -> CreatorProfileResponse:
    user = await db.get(User, user_id)
    if not user:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="User not found")
    return CreatorProfileResponse(
        id=str(user.id),
        user_id=str(user.id),
        name=user.name,
        handle=user.name.lower().replace(" ", "-"),
        bio=None,
        niche=None,
        avatar_url=user.avatar_url,
        follower_count=0,
        total_views=0,
        payout_method=None,
        payout_account=None,
        payout_account_name=None,
        verified=False,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


async def update_profile(db: AsyncSession, user_id: str, payload) -> CreatorProfileResponse:
    user = await db.get(User, user_id)
    if not user:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    await db.commit()
    return await profile(db, user_id)


async def list_series(db: AsyncSession, user_id: str) -> CreatorSeriesResponse:
    result = await db.execute(select(Series).where(Series.creator_id == user_id))
    series = result.scalars().all()
    items = []
    for s in series:
        items.append(CreatorSeriesItem(
            id=str(s.id),
            slug=s.slug,
            title=s.title,
            category=s.category,
            language=s.language,
            total_episodes=s.total_episodes,
            moderation_status=s.moderation_status,
            is_published=s.is_published,
            total_views=0,
            total_unlocks=0,
            earnings_coins=0,
            earnings_naira=0.0,
            created_at=s.created_at.isoformat() if s.created_at else None,
        ))
    return CreatorSeriesResponse(items=items)


async def create_series(db: AsyncSession, user_id: str, payload) -> CreatorSeriesCreateResponse:
    from app.db.models import Episode
    from app.integrations.cloudflare_stream import mint_upload_url
    from app.schemas.creator import CreatorSeriesItem
    series = Series(
        id=str(__import__("uuid").uuid4()),
        slug="my-drama-1",
        title=payload.title,
        synopsis=payload.synopsis,
        cover_url="",
        category=payload.category,
        language=payload.language,
        source="creator",
        creator_id=user_id,
        total_episodes=payload.total_episodes,
    )
    db.add(series)
    await db.flush()
    upload_urls = []
    for i in range(1, payload.total_episodes + 1):
        ep = Episode(
            id=str(__import__("uuid").uuid4()),
            series_id=series.id,
            number=i,
            title=f"Episode {i}",
            synopsis="",
            duration_s=0,
            required_coins=25,
            is_free=False,
        )
        db.add(ep)
        upload_url = await mint_upload_url(str(ep.id))
        upload_urls.append({"episode_number": i, "video_upload_url": upload_url})
    await db.commit()
    series_item = CreatorSeriesItem(
        id=str(series.id),
        slug=series.slug,
        title=series.title,
        category=series.category,
        language=series.language,
        total_episodes=series.total_episodes,
        moderation_status=series.moderation_status,
        is_published=series.is_published,
        created_at=series.created_at.isoformat() if series.created_at else None,
    )
    return CreatorSeriesCreateResponse(series=series_item, upload_urls=upload_urls)


async def update_series(db: AsyncSession, user_id: str, id: str, payload) -> dict:
    from app.core.errors import AppError
    from app.db.models import Episode as EpisodeModel
    series = await db.get(Series, id)
    if not series:
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    if series.creator_id != user_id:
        raise AppError(status_code=403, code="forbidden", detail="Not your series")
    if series.is_published:
        raise AppError(status_code=409, code="already_published", detail="Published series cannot be edited")
    if payload.title is not None:
        series.title = payload.title
    if "synopsis" in payload.model_fields_set:
        series.synopsis = payload.synopsis or ""
    if payload.category is not None:
        series.category = payload.category
    if payload.language is not None:
        series.language = payload.language
    if payload.total_episodes is not None and payload.total_episodes != series.total_episodes:
        existing = (await db.execute(
            select(EpisodeModel).where(EpisodeModel.series_id == series.id)
        )).scalars().all()
        highest = max((e.number for e in existing), default=0)
        from app.integrations.cloudflare_stream import mint_upload_url
        new_urls = []
        for n in range(highest + 1, payload.total_episodes + 1):
            ep = EpisodeModel(
                id=str(__import__("uuid").uuid4()),
                series_id=series.id,
                number=n,
                title=f"Episode {n}",
                synopsis="",
                duration_s=0,
                required_coins=25,
                is_free=False,
            )
            db.add(ep)
            new_urls.append({"episode_number": n, "video_upload_url": await mint_upload_url(str(ep.id))})
        series.total_episodes = payload.total_episodes
        await db.flush()
        await db.commit()
        return {"ok": True, "added_episode_urls": new_urls}
    await db.commit()
    return {"ok": True}


async def submit_for_review(db: AsyncSession, user_id: str, id: str) -> dict:
    from app.core.errors import AppError
    from app.db.models import Episode as EpisodeModel, ModerationItem
    import json as _json
    series = await db.get(Series, id)
    if not series:
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    if series.creator_id != user_id:
        raise AppError(status_code=403, code="forbidden", detail="Not your series")
    if series.moderation_status not in ("draft", "rejected"):
        raise AppError(status_code=409, code="bad_state", detail=f"Cannot submit from moderation_status={series.moderation_status}")
    episodes = (await db.execute(
        select(EpisodeModel).where(EpisodeModel.series_id == series.id)
    )).scalars().all()
    if not episodes:
        raise AppError(status_code=400, code="no_episodes", detail="Add at least one episode before submitting")
    if not all(e.video_ready for e in episodes):
        raise AppError(status_code=400, code="videos_processing", detail="All episodes must finish video processing first")
    series.moderation_status = "pending"
    db.add(ModerationItem(
        id=str(__import__("uuid").uuid4()),
        kind="series",
        ref_id=series.id,
        submitter_id=user_id,
        reason=_json.dumps({"series_id": series.id, "title": series.title}),
        status="pending",
    ))
    await db.commit()
    return {"ok": True, "moderation_status": "pending"}


async def get_upload_url(db: AsyncSession, user_id: str, id: str, n: int) -> dict:
    from app.core.errors import AppError
    from app.db.models import Episode as EpisodeModel
    series = await db.get(Series, id)
    if not series:
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    if series.creator_id != user_id:
        raise AppError(status_code=403, code="forbidden", detail="Not your series")
    episode = (await db.execute(
        select(EpisodeModel).where(
            EpisodeModel.series_id == series.id,
            EpisodeModel.number == n,
        )
    )).scalar_one_or_none()
    if not episode:
        raise AppError(status_code=404, code="not_found", detail=f"No episode {n} on series {id}")
    from app.integrations.cloudflare_stream import mint_upload_url
    return {"episode_number": n, "video_upload_url": await mint_upload_url(str(episode.id))}


async def analytics(db: AsyncSession, user_id: str, range: str) -> dict:
    from datetime import datetime, timedelta
    from app.db.models import Episode
    
    days = 30
    if range == "7d":
        days = 7
    elif range == "90d":
        days = 90
    
    series_result = await db.execute(select(Series).where(Series.creator_id == user_id))
    creator_series = series_result.scalars().all()
    series_ids = [str(s.id) for s in creator_series]
    
    if not series_ids:
        return {"totals": {"views": 0, "unlocks": 0, "earnings_coins": 0}, "daily": [], "by_series": []}
    
    earnings_result = await db.execute(
        select(CreatorEarning).where(CreatorEarning.creator_id == user_id)
    )
    earnings = earnings_result.scalars().all()
    total_coins = sum(e.creator_coins for e in earnings)
    
    episode_ids = set()
    for s in creator_series:
        eps = (await db.execute(
            select(Episode.id).where(Episode.series_id == s.id)
        )).scalars().all()
        episode_ids.update(str(eid) for eid in eps)
    
    by_series = []
    for s in creator_series:
        series_earnings = [e for e in earnings if str(e.episode_id) in episode_ids]
        series_coins = sum(e.creator_coins for e in series_earnings)
        by_series.append({
            "series_id": str(s.id),
            "title": s.title,
            "earnings_coins": series_coins,
            "earnings_naira": series_coins / 10,
            "views": 0,
            "unlocks": len(series_earnings),
        })
    
    return {
        "totals": {"views": 0, "unlocks": len(earnings), "earnings_coins": total_coins},
        "daily": [],
        "by_series": by_series,
    }


async def earnings(db: AsyncSession, user_id: str) -> CreatorEarningsResponse:
    result = await db.execute(select(CreatorEarning).where(CreatorEarning.creator_id == user_id).order_by(CreatorEarning.created_at.desc()))
    earnings = result.scalars().all()
    lifetime_coins = sum(e.creator_coins for e in earnings)
    
    payouts_result = await db.execute(
        select(PayoutRequest).where(
            PayoutRequest.creator_id == user_id,
            PayoutRequest.status.in_(["approved", "paid"])
        )
    )
    payouts = payouts_result.scalars().all()
    payout_coins = sum(p.amount_coins for p in payouts)
    pending_coins = lifetime_coins - payout_coins
    
    transactions = [
        {
            "id": str(e.id),
            "type": "earning",
            "coins": e.creator_coins,
            "naira": e.creator_coins / 10,
            "episode_id": str(e.episode_id),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in earnings
    ]
    
    return CreatorEarningsResponse(
        lifetime={"coins": lifetime_coins, "naira": lifetime_coins / 10},
        pending={"coins": pending_coins, "naira": pending_coins / 10, "availableForPayout": pending_coins >= 50000},
        transactions=transactions,
    )


async def request_payout(db: AsyncSession, user_id: str, payload) -> PayoutResponse:
    from app.core.errors import AppError
    if payload.amount_coins < 50000:
        raise AppError(status_code=400, code="below_minimum", detail="Minimum payout is 50,000 coins")
    
    earnings_result = await db.execute(select(CreatorEarning).where(CreatorEarning.creator_id == user_id))
    earnings = earnings_result.scalars().all()
    total_earned = sum(e.creator_coins for e in earnings)
    payouts_result = await db.execute(
        select(PayoutRequest).where(
            PayoutRequest.creator_id == user_id,
            PayoutRequest.status.in_(["approved", "paid"])
        )
    )
    payouts = payouts_result.scalars().all()
    total_paid = sum(p.amount_coins for p in payouts)
    pending = total_earned - total_paid
    
    if payload.amount_coins > pending:
        raise AppError(status_code=400, code="insufficient_balance", detail="Requested amount exceeds available balance")
    
    payout = PayoutRequest(
        id=str(__import__("uuid").uuid4()),
        creator_id=user_id,
        amount_coins=payload.amount_coins,
        amount_naira=payload.amount_coins / 10,
        status="pending",
        payout_method="Bank",
        payout_account="",
    )
    db.add(payout)
    await db.commit()
    return PayoutResponse(payout={
        "id": str(payout.id),
        "amountCoins": payout.amount_coins,
        "amountNaira": float(payout.amount_naira),
        "status": payout.status,
        "payoutMethod": payout.payout_method,
        "payoutAccount": payout.payout_account,
        "requestedAt": payout.requested_at.isoformat() if payout.requested_at else None,
    })


async def list_payouts(db: AsyncSession, user_id: str) -> PayoutListResponse:
    result = await db.execute(select(PayoutRequest).where(PayoutRequest.creator_id == user_id).order_by(PayoutRequest.requested_at.desc()))
    payouts = result.scalars().all()
    items = [
        PayoutItem(
            id=str(p.id),
            amount_coins=p.amount_coins,
            amount_naira=float(p.amount_naira),
            status=p.status,
            payout_method=p.payout_method,
            payout_account=p.payout_account,
            requested_at=p.requested_at.isoformat() if p.requested_at else None,
            decided_at=p.decided_at.isoformat() if p.decided_at else None,
            decided_by=str(p.decided_by) if p.decided_by else None,
            note=p.note,
        )
        for p in payouts
    ]
    return PayoutListResponse(items=items)