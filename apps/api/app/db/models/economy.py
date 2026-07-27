from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CoinTxn(Base):
    __tablename__ = "coin_txn"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Enum("purchase", "rewarded_ad", "unlock", "refund", "daily_reward", "admin_grant", "admin_refund", "restore", name="coin_txn_reason"), nullable=False)
    ref_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CreatorEarning(Base):
    __tablename__ = "creator_earnings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    creator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    episode_id: Mapped[str] = mapped_column(String(36), nullable=False)
    gross_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    creator_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PayoutRequest(Base):
    __tablename__ = "payout_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    creator_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    amount_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_naira: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "rejected", "paid", "cancelled", name="payout_status"), nullable=False, default="pending")
    payout_method: Mapped[str] = mapped_column(Enum("OPay", "PalmPay", "Moniepoint", "Bank", name="payout_method"), nullable=False)
    payout_account: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class AdImpression(Base):
    __tablename__ = "ad_impressions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ad_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ad_network: Mapped[str] = mapped_column(String(50), nullable=False, default="appLovin")
    ad_type: Mapped[str] = mapped_column(Enum("rewarded", "interstitial", name="ad_type"), nullable=False)
    watched_s: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rewarded_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())