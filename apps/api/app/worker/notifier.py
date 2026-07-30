import asyncio
import json

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.services import notifications as notification_service

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def process_queue(session: AsyncSession, r: aioredis.Redis, raw: bytes) -> None:
    try:
        payload = json.loads(raw)
        event_type = payload.get("type")
        if event_type == "new_episode":
            await notification_service.queue_new_episode(session, payload["episode_id"])
        elif event_type == "payout_decision":
            await notification_service.queue_payout_decision(session, payload["creator_id"], payload["payout_id"], payload["decision"])
    except Exception:
        pass


async def main() -> None:
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    queue = "notifications:queue"
    while True:
        _, raw = await r.blpop(queue, timeout=5)
        if raw:
            async with SessionLocal() as session:
                await process_queue(session, r, raw)


if __name__ == "__main__":
    asyncio.run(main())
