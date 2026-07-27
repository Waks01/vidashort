from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ModerationItem


async def enqueue_series(db: AsyncSession, series_id: str, reason: str, auto_flagged: bool = False):
    item = ModerationItem(
        id=__import__("uuid").uuid4(),
        kind="series",
        ref_id=series_id,
        reason=reason,
        auto_flagged=auto_flagged,
    )
    db.add(item)
    await db.commit()


async def enqueue_comment(db: AsyncSession, comment_id: str, reason: str, auto_flagged: bool = False):
    item = ModerationItem(
        id=__import__("uuid").uuid4(),
        kind="comment",
        ref_id=comment_id,
        reason=reason,
        auto_flagged=auto_flagged,
    )
    db.add(item)
    await db.commit()


async def enqueue_account(db: AsyncSession, user_id: str, reason: str, auto_flagged: bool = False):
    item = ModerationItem(
        id=__import__("uuid").uuid4(),
        kind="account",
        ref_id=user_id,
        reason=reason,
        auto_flagged=auto_flagged,
    )
    db.add(item)
    await db.commit()


async def pending_queue(db: AsyncSession, kind: str | None = None) -> list[ModerationItem]:
    query = select(ModerationItem).where(ModerationItem.status == "pending")
    if kind:
        query = query.where(ModerationItem.kind == kind)
    result = await db.execute(query.order_by(ModerationItem.created_at.desc()))
    return result.scalars().all()