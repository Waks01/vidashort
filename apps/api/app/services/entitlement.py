from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, PaywallRequired
from app.db.models import Episode, WatchHistory
from app.services.paywall import decide, is_vip, pay_with_coins
from app.schemas.entitlement import CheckResponse, UnlockRequest, UnlockResponse


async def check(db: AsyncSession, user_id: str, episode_id: str) -> CheckResponse:
    decision = await decide(db, user_id, episode_id)
    return CheckResponse(
        allowed=decision.get("allowed", False),
        source=decision.get("source"),
        paywall=decision.get("paywall"),
    )


async def unlock(db: AsyncSession, user_id: str, payload: UnlockRequest) -> UnlockResponse:
    source = payload.source
    episode_id = payload.episode_id
    if source == "coins":
        result = await pay_with_coins(db, user_id, episode_id)
        return UnlockResponse(ok=result["ok"], source="coins", coins_after=result.get("coins_after"), creator_credited_coins=result.get("creator_credited_coins"), playback_url=result.get("playback_url"))
    if source == "ad":
        from app.services.ad_cap import record_ad
        result = await record_ad(db, user_id, episode_id)
        return UnlockResponse(ok=result["ok"], source="ad", coins_after=result.get("new_balance"), playback_url=result.get("playback_url"))
    if source == "vip":
        result = await pay_with_vip(db, user_id, episode_id)
        return UnlockResponse(ok=result["ok"], source="vip", playback_url=result.get("playback_url"))
    raise NotImplementedError(f"Unlock source {source} not implemented")


async def pay_with_vip(db: AsyncSession, user_id: str, episode_id: str) -> dict:
    """VIP-granted unlock: verifies an unexpired VipEntitlement exists, stamps
    WatchHistory.unlocked_via_vip, returns the signed playback URL. No coins
    are debited (that's the whole point of VIP) and no creator credit is
    recorded (the subscription flat-fee revenue split is handled elsewhere —
    see `apps/api/app/services/webhooks.py:_activate_vip`).
    """
    if not await is_vip(db, user_id):
        raise PaywallRequired(detail="VIP subscription required")
    episode = (await db.execute(select(Episode).where(Episode.id == episode_id))).scalar_one_or_none()
    if not episode:
        raise AppError(status_code=404, code="not_found", detail="Episode not found")
    from app.integrations.cloudflare_stream import mint_signed_playback_url
    history = (await db.execute(select(WatchHistory).where(
        WatchHistory.user_id == user_id,
        WatchHistory.episode_id == episode.id,
    ))).scalar_one_or_none()
    if history:
        history.unlocked_via_vip = True
    await db.commit()
    playback_url = await mint_signed_playback_url(episode.video_uid)
    return {"ok": True, "source": "vip", "playback_url": playback_url}