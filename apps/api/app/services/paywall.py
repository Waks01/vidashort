from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import VipRequired, InsufficientCoins, AdCapReached, PaywallRequired
from app.db.models import User, VipEntitlement, Episode, Series, WatchHistory, CoinTxn, CreatorEarning


async def is_vip(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(VipEntitlement).where(VipEntitlement.user_id == user_id, VipEntitlement.expires_at > datetime.utcnow())
    )
    return result.scalar_one_or_none() is not None


async def ad_cap_remaining(db: AsyncSession, user_id: str) -> int:
    from app.db.models import AdImpression
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count()).where(AdImpression.user_id == user_id, AdImpression.created_at >= today)
    )
    used = result.scalar_one()
    return max(0, 100 - used)


async def decide(db: AsyncSession, user_id: str, episode_id: str) -> dict:
    user = await db.get(User, user_id)
    episode = (await db.execute(select(Episode).where(Episode.id == episode_id))).scalar_one_or_none()
    if not user or not episode:
        return {"allowed": False}
    series = await db.get(Series, episode.series_id)
    if await is_vip(db, user_id):
        return {"allowed": True, "source": "vip"}
    if episode.is_free or episode.number <= (series.free_episodes if series else 3):
        return {"allowed": True, "source": "free"}
    if user.coins >= 25:
        return {"allowed": True, "source": "coins"}
    remaining_ads = await ad_cap_remaining(db, user_id)
    if remaining_ads > 0:
        return {"allowed": True, "source": "ad", "paywall": {"path": "ad", "cost_coins": 0, "reward_coins": 20, "remaining_ads": remaining_ads, "label": "Watch ad for +20 coins"}}
    return {"allowed": False, "paywall": {"path": "premium", "cost_coins": 0, "reward_coins": 0, "remaining_ads": 0, "label": "Go VIP to keep watching"}}


async def pay_with_coins(db: AsyncSession, user_id: str, episode_id: str) -> dict:
    user = await db.get(User, user_id)
    episode = (await db.execute(select(Episode).where(Episode.id == episode_id))).scalar_one_or_none()
    if not user or not episode:
        raise PaywallRequired(detail="Episode not found")
    series = await db.get(Series, episode.series_id)
    if user.coins < 25:
        raise InsufficientCoins(detail="Not enough coins")
    from app.integrations.cloudflare_stream import mint_signed_playback_url
    user.coins -= 25
    txn = CoinTxn(
        id=__import__("uuid").uuid4(),
        user_id=user.id,
        delta=-25,
        reason="unlock",
        ref_id=episode.id,
        balance_after=user.coins,
    )
    db.add(txn)
    creator_coins = 0
    if series and series.creator_id and series.creator_id != user.id:
        creator = await db.get(User, series.creator_id)
        if creator:
            creator_coins = 15
            creator.loyalty_coins += creator_coins
            earning = CreatorEarning(
                id=__import__("uuid").uuid4(),
                creator_id=creator.id,
                episode_id=episode.id,
                gross_coins=25,
                creator_coins=creator_coins,
            )
            db.add(earning)
    history = (await db.execute(select(WatchHistory).where(WatchHistory.user_id == user.id, WatchHistory.episode_id == episode.id))).scalar_one_or_none()
    if history:
        history.unlocked_via_coins = True
    await db.commit()
    playback_url = await mint_signed_playback_url(episode.video_uid)
    return {"ok": True, "source": "coins", "coins_after": user.coins, "creator_credited_coins": creator_coins, "playback_url": playback_url}