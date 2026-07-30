from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, WatchHistory, CoinTxn, PayoutRequest, CreatorEarning, Series
from app.services import notifications as notif_svc
from app.services import moderation as mod_svc
from app.core.logging import setup_logging
import logging

logger = logging.getLogger(__name__)


async def daily_streak_reset(db: AsyncSession) -> dict:
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    active_user_ids = set(
        str(uid) for uid in (await db.execute(
            select(WatchHistory.user_id).where(WatchHistory.watched_at >= yesterday)
        )).scalars().all()
    )
    all_users = (await db.execute(select(User))).scalars().all()
    reset_count = 0
    for u in all_users:
        if str(u.id) not in active_user_ids:
            if hasattr(u, "streak_day") and u.streak_day:
                u.streak_day = 0
                db.add(u)
                reset_count += 1
    await db.commit()
    logger.info("daily_streak_reset", extra={"reset": reset_count})
    return {"reset": reset_count}


async def daily_revenue_rollup(db: AsyncSession) -> dict:
    from app.services import finance as finance_svc
    yesterday = (datetime.utcnow() - timedelta(days=1))
    result = await finance_svc.daily_revenue(db, yesterday)
    logger.info("daily_revenue_rollup", extra=result)
    return result


async def payout_reminder(db: AsyncSession) -> dict:
    week_ago = datetime.utcnow() - timedelta(days=7)
    pending = (await db.execute(
        select(PayoutRequest).where(PayoutRequest.status == "pending", PayoutRequest.created_at >= week_ago)
    )).scalars().all()
    for p in pending:
        try:
            await notif_svc.queue_payout_decision(db, str(p.user_id), str(p.id), "pending")
        except Exception:
            pass
    logger.info("payout_reminder", extra={"sent": len(pending)})
    return {"sent": len(pending)}


async def content_refresh(db: AsyncSession) -> dict:
    rows = (await db.execute(
        select(Series, func.count(WatchHistory.user_id).label("views"))
        .join(WatchHistory, WatchHistory.episode_id == Series.id)
        .group_by(Series.id)
    )).all()
    updated = 0
    for s, views in rows:
        avg = max(0.0, min(5.0, float(views or 0)))
        if s.rating != avg:
            s.rating = avg
            db.add(s)
            updated += 1
    await db.commit()
    logger.info("content_refresh", extra={"updated": updated})
    return {"updated": updated}


async def run_cron(db: AsyncSession, name: str) -> dict:
    import app.worker.cron as cron_module
    for job in CRON_JOBS:
        if job["name"] == name:
            try:
                return await job["func"](db)
            except Exception as exc:
                logger.exception("cron_job_failed", extra={"job": name})
                raise
    raise ValueError(f"Unknown cron job: {name}")


CRON_JOBS = [
    {"name": "daily_streak_reset", "cron": "0 0 * * *", "func": daily_streak_reset},
    {"name": "daily_revenue_rollup", "cron": "0 1 * * *", "func": daily_revenue_rollup},
    {"name": "payout_reminder", "cron": "0 */6 * * *", "func": payout_reminder},
    {"name": "content_refresh", "cron": "0 */4 * * *", "func": content_refresh},
]
