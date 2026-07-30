"""Paywall service.

Single source of truth for the locked decision order (CLAUDE.md §4):
    VIP → free → coins → ad → premium.

Every router that grants (or denies) episode access goes through `decide()`.
The split math lives in `app.services.revenue_split` — this module just calls it.
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InsufficientCoins, PaywallRequired
from app.db.models import (
    CoinTxn,
    CreatorEarning,
    Episode,
    Series,
    User,
    VipEntitlement,
    WatchHistory,
)
from app.services import ad_cap
from app.services.revenue_split import (
    EPISODE_UNLOCK_COST,
    REWARDED_AD_REWARD,
)


async def is_vip(db: AsyncSession, user_id: str) -> bool:
    """True iff the user has an unexpired VipEntitlement row."""
    result = await db.execute(
        select(VipEntitlement).where(
            VipEntitlement.user_id == user_id,
            VipEntitlement.expires_at > datetime.utcnow(),
        )
    )
    return result.scalar_one_or_none() is not None


async def decide(db: AsyncSession, user_id: str, episode_id: str) -> dict:
    """Run the locked decision order. Returns a dict the entitlement router
    wraps in `CheckResponse`.

    Decision flow (locked):
      1. VIP → unlock
      2. Episode is free OR is within the series' free window → unlock
      3. User has ≥ EPISODE_UNLOCK_COST coins → unlock via coins
      4. Daily ad cap has remaining impressions → show the rewarded-ad paywall
      5. Otherwise → premium upsell paywall
    """
    user = await db.get(User, user_id)
    episode = (await db.execute(select(Episode).where(Episode.id == episode_id))).scalar_one_or_none()
    if not user or not episode:
        return {"allowed": False}
    series = await db.get(Series, episode.series_id)
    if await is_vip(db, user_id):
        return {"allowed": True, "source": "vip"}
    if episode.is_free or episode.number <= (series.free_episodes if series else 3):
        return {"allowed": True, "source": "free"}
    if user.coins >= EPISODE_UNLOCK_COST:
        return {"allowed": True, "source": "coins"}
    remaining_ads = await ad_cap.remaining(db, user_id)
    if remaining_ads > 0:
        return {
            "allowed": True,
            "source": "ad",
            "paywall": {
                "path": "ad",
                "cost_coins": 0,
                "reward_coins": REWARDED_AD_REWARD,
                "remaining_ads": remaining_ads,
                "label": f"Watch ad for +{REWARDED_AD_REWARD} coins",
            },
        }
    return {
        "allowed": False,
        "paywall": {
            "path": "premium",
            "cost_coins": 0,
            "reward_coins": 0,
            "remaining_ads": 0,
            "label": "Go VIP to keep watching",
        },
    }


async def pay_with_coins(db: AsyncSession, user_id: str, episode_id: str) -> dict:
    """Unlock an episode by deducting EPISODE_UNLOCK_COST coins from the user
    and crediting the creator their 60% share (locked 60/40 split from
    `app.services.revenue_split`). Also stamps WatchHistory and returns the
    signed playback URL.
    """
    user = await db.get(User, user_id)
    episode = (await db.execute(select(Episode).where(Episode.id == episode_id))).scalar_one_or_none()
    if not user or not episode:
        raise PaywallRequired(detail="Episode not found")
    series = await db.get(Series, episode.series_id)
    if user.coins < EPISODE_UNLOCK_COST:
        raise InsufficientCoins(detail="Not enough coins")
    from app.integrations.cloudflare_stream import mint_signed_playback_url
    user.coins -= EPISODE_UNLOCK_COST
    txn = CoinTxn(
        id=str(uuid.uuid4()),
        user_id=user.id,
        delta=-EPISODE_UNLOCK_COST,
        reason="unlock",
        ref_id=episode.id,
        balance_after=user.coins,
    )
    db.add(txn)
    creator_coins = 0
    if series and series.creator_id and series.creator_id != user.id:
        creator_coins = await credit_creator(db, series.creator_id, EPISODE_UNLOCK_COST, episode.id)
    history = (await db.execute(select(WatchHistory).where(
        WatchHistory.user_id == user.id,
        WatchHistory.episode_id == episode.id,
    ))).scalar_one_or_none()
    if history:
        history.unlocked_via_coins = True
    await db.commit()
    playback_url = await mint_signed_playback_url(episode.video_uid)
    return {
        "ok": True,
        "source": "coins",
        "coins_after": user.coins,
        "creator_credited_coins": creator_coins,
        "playback_url": playback_url,
    }


async def pay_with_ad(db: AsyncSession, user_id: str, episode_id: str) -> dict:
    """Unlock an episode via rewarded ad: credit REWARDED_AD_REWARD coins to user,
    record AdImpression, stamp WatchHistory.unlocked_via_ad, return signed playback URL.
    """
    from app.core.errors import AppError
    from app.db.models import AdImpression, CoinTxn, WatchHistory
    user = await db.get(User, user_id)
    episode = (await db.execute(select(Episode).where(Episode.id == episode_id))).scalar_one_or_none()
    if not user or not episode:
        raise PaywallRequired(detail="Episode not found")
    from app.integrations.cloudflare_stream import mint_signed_playback_url
    ad_id = f"ad_{uuid.uuid4().hex[:8]}"
    impression = AdImpression(
        id=str(uuid.uuid4()),
        user_id=user_id,
        ad_id=ad_id,
        ad_network="appLovin",
        ad_type="rewarded",
        watched_s=15,
        completed=True,
        rewarded_coins=REWARDED_AD_REWARD,
    )
    db.add(impression)
    user.coins += REWARDED_AD_REWARD
    txn = CoinTxn(
        id=str(uuid.uuid4()),
        user_id=user.id,
        delta=REWARDED_AD_REWARD,
        reason="rewarded_ad",
        ref_id=impression.id,
        balance_after=user.coins,
    )
    db.add(txn)
    history = (await db.execute(select(WatchHistory).where(
        WatchHistory.user_id == user.id,
        WatchHistory.episode_id == episode.id,
    ))).scalar_one_or_none()
    if history:
        history.unlocked_via_ad = True
    await db.commit()
    playback_url = await mint_signed_playback_url(episode.video_uid)
    return {
        "ok": True,
        "source": "ad",
        "coins_after": user.coins,
        "playback_url": playback_url,
    }
