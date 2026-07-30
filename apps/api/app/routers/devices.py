from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.devices import DeviceRegisterRequest, DeviceResponse
from app.services import devices as device_service

router = APIRouter()


@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: DeviceRegisterRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await device_service.register(db, user["id"], payload)


@router.post("/{id}/unregister", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await device_service.unregister(db, user["id"], id)
    return {}
