import hashlib
import hmac

from app.core.errors import AppError


def verify_signature(secret: str, body: bytes, header: str) -> bool:
    if not secret or not header:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


async def handle_cloudflare(db, payload: dict):
    from app.db.models import Episode
    from sqlalchemy import select
    uid = payload.get("uid")
    if not uid:
        return
    result = await db.execute(select(Episode).where(Episode.video_uid == uid))
    episode = result.scalar_one_or_none()
    if episode:
        episode.video_ready = True
        await db.commit()


async def handle_revenuecat(db, payload: dict):
    raise NotImplementedError("RevenueCat webhook not implemented yet")


async def handle_apple(db, payload: dict):
    raise NotImplementedError("Apple webhook not implemented yet")


async def handle_google(db, payload: dict):
    raise NotImplementedError("Google webhook not implemented yet")