from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VipEntitlement


async def sync_subscription(db: AsyncSession, user_id: str, event: dict[str, Any]):
    event_type = event.get("type")
    product_id = event.get("product_id")
    expires_at = event.get("expires_at")
    original_txn_id = event.get("original_transaction_id")
    if event_type in ("INITIAL_PURCHASE", "RENEWAL"):
        entitlement = VipEntitlement(
            user_id=user_id,
            source="revenuecat",
            product_id=product_id,
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() if not expires_at else expires_at,
            original_txn_id=original_txn_id,
        )
        db.add(entitlement)
    elif event_type == "CANCELLATION":
        result = await db.execute(select(VipEntitlement).where(VipEntitlement.user_id == user_id, VipEntitlement.source == "revenuecat"))
        ent = result.scalar_one_or_none()
        if ent:
            ent.auto_renew = False
    elif event_type == "EXPIRATION":
        await db.execute(select(VipEntitlement).where(VipEntitlement.user_id == user_id, VipEntitlement.source == "revenuecat"))
    await db.commit()