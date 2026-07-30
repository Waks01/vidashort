from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.models import PushToken, Series, Episode


async def queue_new_episode(db: AsyncSession, episode_id: str) -> None:
    from app.integrations.fcm import send_push as fcm_send
    from app.integrations.apns import send_push as apns_send
    episode = await db.get(Episode, episode_id)
    if not episode:
        return
    series = await db.get(Series, episode.series_id)
    if not series:
        return
    tokens = (await db.execute(select(PushToken).where(PushToken.active == True))).scalars().all()
    title = f"New episode: {series.title}"
    body = f"Episode {episode.number} - {episode.title}"
    data = {"type": "new_episode", "series_id": str(series.id), "episode_id": str(episode.id), "episode_number": str(episode.number)}
    for t in tokens:
        if t.platform == "android":
            await fcm_send(t.token, title, body, data)
        elif t.platform == "ios":
            await apns_send(t.token, title, body, data)


async def queue_payout_decision(db: AsyncSession, creator_id: str, payout_id: str, decision: str) -> None:
    from app.integrations.fcm import send_push as fcm_send
    from app.integrations.apns import send_push as apns_send
    tokens = (await db.execute(select(PushToken).where(PushToken.user_id == creator_id, PushToken.active == True))).scalars().all()
    title = "Payout update"
    body = f"Your payout request has been {decision}"
    data = {"type": "payout_decision", "payout_id": payout_id, "decision": decision}
    for t in tokens:
        if t.platform == "android":
            await fcm_send(t.token, title, body, data)
        elif t.platform == "ios":
            await apns_send(t.token, title, body, data)


async def list_user_notifications(db: AsyncSession, user_id: str) -> list[dict]:
    now = datetime.utcnow()
    tokens = (await db.execute(select(PushToken).where(PushToken.user_id == user_id, PushToken.active == True))).scalars().all()
    items = []
    for t in tokens:
        items.append({
            "id": str(t.id),
            "type": "pushed_token",
            "body": f"{t.platform} push token registered",
            "timeAgo": t.created_at.isoformat() if t.created_at else now.isoformat(),
            "read": True,
            "platform": t.platform,
        })
    return items


async def mark_read(db: AsyncSession, user_id: str, notif_id: str) -> None:
    await db.commit()
