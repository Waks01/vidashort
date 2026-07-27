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
    return CreatorSeriesResponse(items=[])


async def create_series(db: AsyncSession, user_id: str, payload) -> CreatorSeriesCreateResponse:
    from app.db.models import Episode
    from app.integrations.cloudflare_stream import mint_upload_url
    from app.schemas.creator import CreatorSeriesItem
    series = Series(
        id=__import__("uuid").uuid4(),
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
            id=__import__("uuid").uuid4(),
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
    raise NotImplementedError("Update series not implemented yet")


async def submit_for_review(db: AsyncSession, user_id: str, id: str) -> dict:
    raise NotImplementedError("Submit for review not implemented yet")


async def get_upload_url(db: AsyncSession, user_id: str, id: str, n: int) -> dict:
    raise NotImplementedError("Get upload URL not implemented yet")


async def analytics(db: AsyncSession, user_id: str, range: str) -> dict:
    return {"totals": {}, "daily": [], "by_series": []}


async def earnings(db: AsyncSession, user_id: str) -> CreatorEarningsResponse:
    result = await db.execute(select(CreatorEarning).where(CreatorEarning.creator_id == user_id))
    earnings = result.scalars().all()
    lifetime_coins = sum(e.creator_coins for e in earnings)
    return CreatorEarningsResponse(
        lifetime={"coins": lifetime_coins, "naira": lifetime_coins / 10},
        pending={"coins": lifetime_coins, "naira": lifetime_coins / 10, "availableForPayout": lifetime_coins >= 50000},
        transactions=[],
    )


async def request_payout(db: AsyncSession, user_id: str, payload) -> PayoutResponse:
    from app.core.errors import AppError
    if payload.amount_coins < 50000:
        raise AppError(status_code=400, code="below_minimum", detail="Minimum payout is 50,000 coins")
    payout = PayoutRequest(
        id=__import__("uuid").uuid4(),
        creator_id=user_id,
        amount_coins=payload.amount_coins,
        amount_naira=payload.amount_coins / 10,
        status="pending",
        payout_method="Bank",
        payout_account="",
    )
    db.add(payout)
    await db.commit()
    return PayoutResponse(payout={"id": str(payout.id), "amountCoins": payout.amount_coins, "amountNaira": float(payout.amount_naira), "status": payout.status, "payoutMethod": payout.payout_method, "payoutAccount": payout.payout_account, "requestedAt": payout.requested_at.isoformat() if payout.requested_at else None})


async def list_payouts(db: AsyncSession, user_id: str) -> PayoutListResponse:
    result = await db.execute(select(PayoutRequest).where(PayoutRequest.creator_id == user_id).order_by(PayoutRequest.requested_at.desc()))
    payouts = result.scalars().all()
    return PayoutListResponse(items=[])