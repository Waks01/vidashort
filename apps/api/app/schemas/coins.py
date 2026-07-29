from app.core.pydantic_base import BaseSchema


class CoinTxnItem(BaseSchema):
    id: str
    delta: int
    reason: str
    ref_id: str | None = None
    balance_after: int
    created_at: str


class BalanceResponse(BaseSchema):
    coins: int
    lifetime_purchased: int
    lifetime_spent: int
    lifetime_earned_ads: int
    lifetime_earned_daily: int
    recent: list[CoinTxnItem]


class PackItem(BaseSchema):
    id: str
    coins: int
    bonus_coins: int
    total_coins: int
    price_naira: int
    price_formatted: str
    badge: str | None = None
    apple_product_id: str
    google_product_id: str


class PacksResponse(BaseSchema):
    packs: list[PackItem]


class PurchaseReceipt(BaseSchema):
    provider: str
    data: str
    txn_id: str


class PurchaseRequest(BaseSchema):
    pack_id: str
    receipt: PurchaseReceipt


class PurchaseResponse(BaseSchema):
    coins: int
    txn_id: str
    credited_coins: int
    bonus_coins: int