from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.user import AgeConfirmRequest, MeResponse, UpdateMeRequest
from app.services import me as me_service

router = APIRouter()


@router.get("", response_model=MeResponse)
async def get_me(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await me_service.get_me(db, user["id"])


@router.patch("", response_model=MeResponse)
async def update_me(
    payload: UpdateMeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await me_service.update_me(db, user["id"], payload)


@router.post("/age-confirm", status_code=status.HTTP_204_NO_CONTENT)
async def age_confirm(
    payload: AgeConfirmRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await me_service.age_confirm(db, user["id"], payload.confirmed)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await me_service.delete_me(db, user["id"])