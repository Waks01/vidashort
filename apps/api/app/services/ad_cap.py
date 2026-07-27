from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdImpression


async def remaining(db: AsyncSession, user_id: str) -> int:
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count()).where(AdImpression.user_id == user_id, AdImpression.created_at >= today)
    )
    used = result.scalar_one()
    return max(0, 100 - used)