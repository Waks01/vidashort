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

    lifetime_purchased = (await db.execute(
        select(func.coalesce(func.sum(CoinTxn.delta), 0)).where(CoinTxn.user_id == user_id, CoinTxn.reason == "purchase", CoinTxn.delta > 0)
    )).scalar_one()

    lifetime_spent = (await db.execute(
        select(func.coalesce(func.sum(-CoinTxn.delta), 0)).where(CoinTxn.user_id == user_id, CoinTxn.reason == "unlock", CoinTxn.delta < 0)
    )).scalar_one()

    lifetime_earned_ads = (await db.execute(
        select(func.coalesce(func.sum(CoinTxn.delta), 0)).where(CoinTxn.user_id == user_id, CoinTxn.reason == "rewarded_ad")
    )).scalar_one()

    lifetime_earned_daily = (await db.execute(
        select(func.coalesce(func.sum(CoinTxn.delta), 0)).where(CoinTxn.user_id == user_id, CoinTxn.reason == "daily_reward")
    )).scalar_one()

    return BalanceResponse(
        coins=user.coins,
        lifetime_purchased=lifetime_purchased,
        lifetime_spent=lifetime_spent,
        lifetime_earned_ads=lifetime_earned_ads,
        lifetime_earned_daily=lifetime_earned_daily,
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
    from app.db.models import User, CoinTxn
    from app.services.revenue_split import COINS_PER_NAIRA

    user = await db.get(User, user_id)
    if not user:
        raise AppError(status_code=404, code="not_found", detail="User not found")

    if payload.receipt.provider == "apple":
        from app.integrations.apple import verify_receipt
        result = await verify_receipt(payload.receipt.data)
        if not result.get("valid"):
            raise AppError(status_code=400, code="invalid_receipt", detail="Apple receipt verification failed")
        product_id = result.get("product_id", "")
        txn_id = result.get("original_txn_id") or payload.receipt.txn_id
    elif payload.receipt.provider == "google":
        from app.integrations.google import verify_purchase
        result = await verify_purchase(payload.receipt.data, "com.vidashort.app", payload.pack_id)
        if not result.get("valid"):
            raise AppError(status_code=400, code="invalid_receipt", detail="Google purchase verification failed")
        product_id = result.get("product_id", "")
        txn_id = result.get("purchase_token") or payload.receipt.txn_id
    elif payload.receipt.provider == "revenuecat":
        from app.integrations.revenuecat import fetch_subscriber_info
        sub = await fetch_subscriber_info(user_id)
        if not sub or not sub.get("entitlements"):
            raise AppError(status_code=400, code="invalid_receipt", detail="RevenueCat verification failed")
        product_id = "vip_monthly"
        txn_id = payload.receipt.txn_id
    else:
        raise AppError(status_code=400, code="unsupported_provider", detail=f"Provider {payload.receipt.provider} not supported")

    existing = (await db.execute(select(CoinTxn).where(CoinTxn.ref_id == txn_id))).scalar_one_or_none()
    if existing:
        raise AppError(status_code=409, code="already_charged", detail="This receipt was already used")

    packs = {
        "pack_100": {"coins": 100, "bonus": 0},
        "pack_500": {"coins": 500, "bonus": 0},
        "pack_2200": {"coins": 2000, "bonus": 200},
        "pack_6000": {"coins": 5000, "bonus": 1000},
        "pack_19000": {"coins": 15000, "bonus": 4000},
    }
    pack = packs.get(payload.pack_id)
    if not pack:
        raise AppError(status_code=404, code="pack_not_found", detail=f"Pack {payload.pack_id} not found")

    total_coins = pack["coins"] + pack["bonus"]
    user.coins += total_coins
    txn = CoinTxn(
        id=str(__import__("uuid").uuid4()),
        user_id=user.id,
        delta=total_coins,
        reason="purchase",
        ref_id=txn_id,
        balance_after=user.coins,
    )
    db.add(txn)
    await db.commit()

    return {
        "coins": user.coins,
        "txnId": str(txn.id),
        "creditedCoins": pack["coins"],
        "bonusCoins": pack["bonus"],
    }