from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.paywall import decide, pay_with_coins
from app.schemas.entitlement import CheckResponse, UnlockRequest, UnlockResponse


async def check(db: AsyncSession, user_id: str, episode_id: str) -> CheckResponse:
    decision = await decide(db, user_id, episode_id)
    return CheckResponse(allowed=decision.get("allowed", False), source=decision.get("source"))


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
    raise NotImplementedError("VIP unlock not implemented yet")