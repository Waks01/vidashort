from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.models import Series, ModerationItem

NSFW_KEYWORDS = ["nsfw", "xxx", "porn", "nude", "explicit"]
VIOLENCE_KEYWORDS = ["kill", "murder", "blood", "torture", "rape"]
HATE_KEYWORDS = ["hate", "racist", "bigot", "slur"]


def _auto_flag_score(text: str) -> tuple[float, list[str]]:
    lower = text.lower()
    hits = []
    for kw in NSFW_KEYWORDS:
        if kw in lower:
            hits.append(kw)
    for kw in VIOLENCE_KEYWORDS:
        if kw in lower:
            hits.append(kw)
    for kw in HATE_KEYWORDS:
        if kw in lower:
            hits.append(kw)
    score = min(1.0, len(hits) * 0.3)
    return score, hits


async def auto_flag_series(db: AsyncSession, series: Series) -> None:
    text = f"{series.title} {series.synopsis}"
    score, hits = _auto_flag_score(text)
    if score >= 0.6:
        existing = await db.execute(select(ModerationItem).where(ModerationItem.ref_id == str(series.id), ModerationItem.kind == "series"))
        if existing.scalar_one_or_none():
            return
        db.add(ModerationItem(
            id=str(__import__("uuid").uuid4()),
            kind="series",
            ref_id=str(series.id),
            submitter_id=None,
            reason=f"Auto-flagged keywords: {', '.join(hits)}",
            status="pending",
            auto_flagged=True,
        ))
        await db.commit()


async def auto_flag_comment(db: AsyncSession, comment_id: str, body: str) -> None:
    score, hits = _auto_flag_score(body)
    if score >= 0.6:
        existing = await db.execute(select(ModerationItem).where(ModerationItem.ref_id == comment_id, ModerationItem.kind == "comment"))
        if existing.scalar_one_or_none():
            return
        db.add(ModerationItem(
            id=str(__import__("uuid").uuid4()),
            kind="comment",
            ref_id=comment_id,
            submitter_id=None,
            reason=f"Auto-flagged keywords: {', '.join(hits)}",
            status="pending",
            auto_flagged=True,
        ))
        await db.commit()
