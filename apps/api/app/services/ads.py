"""Rewarded-ad service: record ad impressions, mint the coin reward.

This is the S2S callback surface — AppLovin/AdMob hit /v1/ads/record with
the user's impression and we credit coins, subject to the daily cap.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import AdImpression, CoinTxn, User
from app.schemas.ads import AdRecordResponse
from app.services import ad_cap
from app.services.revenue_split import REWARDED_AD_REWARD


async def record_ad(db: AsyncSession, user_id: str, payload) -> AdRecordResponse:
    """Validate the impression, dedupe by ad_id, credit REWARDED_AD_REWARD coins,
    and return the new balance + remaining cap.
    """
    if payload.watched_s < 5:
        raise AppError(status_code=400, code="watched_too_short", detail="Ad watched too short")
    existing = (await db.execute(
        select(AdImpression).where(
            AdImpression.user_id == user_id,
            AdImpression.ad_id == payload.ad_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise AppError(status_code=400, code="already_recorded", detail="Ad already recorded")
    if (await ad_cap.remaining(db, user_id)) <= 0:
        raise AppError(status_code=429, code="cap_reached", detail="Daily ad cap reached")
    impression = AdImpression(
        id=str(uuid.uuid4()),
        user_id=user_id,
        ad_id=payload.ad_id,
        ad_network="appLovin",
        ad_type="rewarded",
        watched_s=payload.watched_s,
        completed=payload.completed,
        rewarded_coins=REWARDED_AD_REWARD,
    )
    db.add(impression)
    user = await db.get(User, user_id)
    if user:
        user.coins += REWARDED_AD_REWARD
        # Append-only ledger entry — keeps `coin_txn` the source of truth for
        # balance history (reconstruct any user's balance from this table).
        db.add(CoinTxn(
            id=str(uuid.uuid4()),
            user_id=user.id,
            delta=REWARDED_AD_REWARD,
            reason="rewarded_ad",
            ref_id=impression.id,
            balance_after=user.coins,
        ))
    await db.commit()
    return AdRecordResponse(
        ok=True,
        rewarded_coins=REWARDED_AD_REWARD,
        new_balance=user.coins if user else 0,
        remaining=await ad_cap.remaining(db, user_id),
    )