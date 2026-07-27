from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.models import User, Series, ModerationItem, PayoutRequest, CoinTxn, AuditLog
from app.schemas.admin import (
    AdminAdCampaignItem,
    AdminFinanceResponse,
    AdminModerationDecideRequest,
    AdminModerationResponse,
    AdminOverviewResponse,
    AdminPayoutDecideRequest,
    AdminUserUpdateRequest,
)


async def overview(db: AsyncSession, range: str) -> AdminOverviewResponse:
    return AdminOverviewResponse(
        gmv_naira=0.0,
        net_revenue_naira=0.0,
        dau=0,
        mau=0,
        new_signups=0,
        paying_users=0,
        active_vip=0,
        ad_cap_hits=0,
        moderation_queue_size=0,
        pending_payouts_naira=0.0,
        top_series=[],
    )


async def moderation(db: AsyncSession, kind, status, cursor, limit) -> AdminModerationResponse:
    return AdminModerationResponse(items=[], next_cursor=None)


async def moderation_decide(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    raise NotImplementedError("Moderation decide not implemented yet")


async def content_list(db: AsyncSession, cursor, source, q, category, moderation_status) -> dict:
    return {"items": [], "next_cursor": None}


async def content_update(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    raise NotImplementedError("Content update not implemented yet")


async def content_feature(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    raise NotImplementedError("Content feature not implemented yet")


async def user_list(db: AsyncSession, cursor, role, q, banned) -> dict:
    return {"items": [], "next_cursor": None}


async def user_detail(db: AsyncSession, id: str) -> dict:
    user = await db.get(User, id)
    if not user:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="User not found")
    return {"user": {"id": str(user.id), "email": user.email, "name": user.name, "role": user.role, "coins": user.coins}}


async def user_update(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    raise NotImplementedError("User update not implemented yet")


async def ad_campaigns(db: AsyncSession) -> list[AdminAdCampaignItem]:
    return []


async def ad_campaign_update(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    raise NotImplementedError("Ad campaign update not implemented yet")


async def finance(db: AsyncSession, range: str) -> AdminFinanceResponse:
    return AdminFinanceResponse(
        net_revenue_naira=0.0,
        gross_coin_sales_naira=0.0,
        creator_liability_naira=0.0,
        platform_net_naira=0.0,
        ledger=[],
    )


async def payout_decide(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    raise NotImplementedError("Payout decide not implemented yet")