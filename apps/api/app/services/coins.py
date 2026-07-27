from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, CoinTxn
from app.schemas.coins import BalanceResponse, CoinTxnItem, PacksResponse


async def balance(db: AsyncSession, user_id: str) -> BalanceResponse:
    user = await db.get(User, user_id)
    if not user:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="User not found")
    result = await db.execute(select(CoinTxn).where(CoinTxn.user_id == user_id).order_by(CoinTxn.created_at.desc()).limit(20))
    txns = [
        CoinTxnItem(
            id=str(t.id),
            delta=t.delta,
            reason=t.reason,
            ref_id=str(t.ref_id) if t.ref_id else None,
            balance_after=t.balance_after,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in result.scalars().all()
    ]
    return BalanceResponse(
        coins=user.coins,
        lifetime_purchased=0,
        lifetime_spent=0,
        lifetime_earned_ads=0,
        lifetime_earned_daily=0,
        recent=txns,
    )


async def packs(db: AsyncSession) -> PacksResponse:
    from app.schemas.coins import PackItem
    packs = [
        PackItem(id="pack_100", coins=100, bonus_coins=0, total_coins=100, price_naira=100, price_formatted="₦100", badge=None, apple_product_id="vs.coins.100", google_product_id="vs_coins_100"),
        PackItem(id="pack_500", coins=500, bonus_coins=0, total_coins=500, price_naira=500, price_formatted="₦500", badge=None, apple_product_id="vs.coins.500", google_product_id="vs_coins_500"),
        PackItem(id="pack_2200", coins=2000, bonus_coins=200, total_coins=2200, price_naira=2000, price_formatted="₦2,000", badge="Best Value", apple_product_id="vs.coins.2200", google_product_id="vs_coins_2200"),
        PackItem(id="pack_6000", coins=5000, bonus_coins=1000, total_coins=6000, price_naira=5000, price_formatted="₦5,000", badge=None, apple_product_id="vs.coins.6000", google_product_id="vs_coins_6000"),
        PackItem(id="pack_19000", coins=15000, bonus_coins=4000, total_coins=19000, price_naira=15000, price_formatted="₦15,000", badge="Most Popular", apple_product_id="vs.coins.19000", google_product_id="vs_coins_19000"),
    ]
    return PacksResponse(packs=packs)


async def purchase(db: AsyncSession, user_id: str, payload) -> dict:
    from app.core.errors import AppError
    raise AppError(status_code=501, detail="IAP receipt verification not implemented")