from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin
from app.db.session import get_db
from app.schemas.admin import (
    AdminAdCampaignItem,
    AdminFinanceResponse,
    AdminModerationDecideRequest,
    AdminModerationResponse,
    AdminOverviewResponse,
    AdminPayoutDecideRequest,
    AdminUserUpdateRequest,
)
from app.services import admin as admin_service

router = APIRouter()


@router.get("/overview", response_model=AdminOverviewResponse)
async def overview(
    range: str = Query("24h"),
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.overview(db, range)


@router.get("/moderation", response_model=AdminModerationResponse)
async def moderation(
    kind: str | None = Query(None),
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20),
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.moderation(db, kind, status, cursor, limit)


@router.post("/moderation/{id}/decide")
async def moderation_decide(
    id: str,
    payload: AdminModerationDecideRequest,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.moderation_decide(db, user["id"], id, payload)


@router.get("/content")
async def content_list(
    cursor: str | None = Query(None),
    source: str | None = Query(None),
    q: str | None = Query(None),
    category: str | None = Query(None),
    moderation_status: str | None = Query(None),
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.content_list(db, cursor, source, q, category, moderation_status)


@router.patch("/content/{id}")
async def content_update(
    id: str,
    payload: dict,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.content_update(db, user["id"], id, payload)


@router.post("/content/{id}/feature")
async def content_feature(
    id: str,
    payload: dict,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.content_feature(db, user["id"], id, payload)


@router.get("/users")
async def user_list(
    cursor: str | None = Query(None),
    role: str | None = Query(None),
    q: str | None = Query(None),
    banned: bool | None = Query(None),
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.user_list(db, cursor, role, q, banned)


@router.get("/users/{id}")
async def user_detail(
    id: str,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.user_detail(db, id)


@router.patch("/users/{id}")
async def user_update(
    id: str,
    payload: AdminUserUpdateRequest,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.user_update(db, user["id"], id, payload)


@router.get("/ads", response_model=list[AdminAdCampaignItem])
async def ad_campaigns(
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.ad_campaigns(db)


@router.patch("/ads/{id}")
async def ad_campaign_update(
    id: str,
    payload: dict,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.ad_campaign_update(db, user["id"], id, payload)


@router.get("/finance", response_model=AdminFinanceResponse)
async def finance(
    range: str = Query("7d"),
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.finance(db, range)


@router.post("/payouts/{id}/decide")
async def payout_decide(
    id: str,
    payload: AdminPayoutDecideRequest,
    user: dict = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.payout_decide(db, user["id"], id, payload)