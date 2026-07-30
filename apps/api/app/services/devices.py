from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.errors import AppError
from app.db.models import PushToken


async def register(db: AsyncSession, user_id: str, payload) -> dict:
    from app.schemas.devices import DeviceResponse
    existing = await db.execute(select(PushToken).where(PushToken.token == payload.token, PushToken.active == True))
    token_row = existing.scalar_one_or_none()
    if token_row:
        token_row.user_id = user_id
        token_row.platform = payload.platform
        await db.commit()
        return {"id": str(token_row.id), "platform": token_row.platform}
    token_row = PushToken(id=str(uuid.uuid4()), user_id=user_id, token=payload.token, platform=payload.platform, active=True)
    db.add(token_row)
    await db.commit()
    return {"id": str(token_row.id), "platform": payload.platform}


async def unregister(db: AsyncSession, user_id: str, id: str) -> None:
    token_row = await db.get(PushToken, id)
    if not token_row or token_row.user_id != user_id:
        raise AppError(status_code=404, code="not_found", detail="Device not found")
    token_row.active = False
    await db.commit()
