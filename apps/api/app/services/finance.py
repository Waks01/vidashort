from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.models import CoinTxn, CreatorEarning


async def daily_revenue(db: AsyncSession, since: datetime) -> dict:
    end = since + timedelta(days=1)
    sales = await db.execute(
        select(func.sum(CoinTxn.delta)).where(CoinTxn.reason == "purchase", CoinTxn.created_at >= since, CoinTxn.created_at < end)
    )
    gross_coins = max(0, sales.scalar_one() or 0)
    earnings = await db.execute(
        select(func.sum(CreatorEarning.creator_coins)).where(CreatorEarning.created_at >= since, CreatorEarning.created_at < end)
    )
    liability = max(0, earnings.scalar_one() or 0)
    return {
        "date": since.date().isoformat(),
        "gross_coins": gross_coins,
        "gross_naira": gross_coins / 10,
        "creator_liability_coins": liability,
        "creator_liability_naira": liability / 10,
        "platform_net_naira": (gross_coins - liability) / 10,
    }


async def creator_liability(db: AsyncSession) -> dict:
    total = await db.execute(select(func.sum(CreatorEarning.creator_coins)))
    coins = max(0, total.scalar_one() or 0)
    return {"coins": coins, "naira": coins / 10}


async def platform_net(db: AsyncSession, since: datetime) -> float:
    sales = await db.execute(select(func.sum(CoinTxn.delta)).where(CoinTxn.reason == "purchase", CoinTxn.created_at >= since))
    earnings = await db.execute(select(func.sum(CreatorEarning.creator_coins)).where(CreatorEarning.created_at >= since))
    gross = max(0, sales.scalar_one() or 0)
    liab = max(0, earnings.scalar_one() or 0)
    return (gross - liab) / 10
