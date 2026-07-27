from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.coins import (
    BalanceResponse,
    PacksResponse,
    PurchaseRequest,
    PurchaseResponse,
)
from app.services import coins as coin_service

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def balance(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await coin_service.balance(db, user["id"])


@router.get("/packs", response_model=PacksResponse)
async def packs(db: AsyncSession = Depends(get_db)):
    return await coin_service.packs(db)


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase(
    payload: PurchaseRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await coin_service.purchase(db, user["id"], payload)