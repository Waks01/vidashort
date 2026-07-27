from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_creator
from app.db.session import get_db
from app.schemas.creator import (
    CreatorAnalyticsResponse,
    CreatorEarningsResponse,
    CreatorProfileRequest,
    CreatorProfileResponse,
    CreatorSeriesCreateRequest,
    CreatorSeriesCreateResponse,
    CreatorSeriesResponse,
    PayoutListResponse,
    PayoutRequest,
    PayoutResponse,
)
from app.services import creator as creator_service

router = APIRouter()


@router.get("/profile", response_model=CreatorProfileResponse)
async def profile(
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.profile(db, user["id"])


@router.patch("/profile", response_model=CreatorProfileResponse)
async def update_profile(
    payload: CreatorProfileRequest,
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.update_profile(db, user["id"], payload)


@router.get("/series", response_model=CreatorSeriesResponse)
async def list_series(
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.list_series(db, user["id"])


@router.post("/series", response_model=CreatorSeriesCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_series(
    payload: CreatorSeriesCreateRequest,
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.create_series(db, user["id"], payload)


@router.patch("/series/{id}", response_model=CreatorSeriesResponse)
async def update_series(
    id: str,
    payload: dict,
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.update_series(db, user["id"], id, payload)


@router.post("/series/{id}/submit-for-review")
async def submit_for_review(
    id: str,
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.submit_for_review(db, user["id"], id)


@router.get("/series/{id}/episodes/{n}/upload")
async def get_upload_url(
    id: str,
    n: int,
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.get_upload_url(db, user["id"], id, n)


@router.get("/analytics")
async def analytics(
    range: str = Query("7d"),
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.analytics(db, user["id"], range)


@router.get("/earnings", response_model=CreatorEarningsResponse)
async def earnings(
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.earnings(db, user["id"])


@router.post("/payouts", response_model=PayoutResponse, status_code=status.HTTP_201_CREATED)
async def request_payout(
    payload: PayoutRequest,
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.request_payout(db, user["id"], payload)


@router.get("/payouts", response_model=PayoutListResponse)
async def list_payouts(
    user: dict = Depends(get_creator),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.list_payouts(db, user["id"])