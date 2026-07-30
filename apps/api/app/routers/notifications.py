from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.user import MeResponse

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_notifications(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.db.models import PushToken
    from app.services import notifications as svc
    return await svc.list_user_notifications(db, user["id"])


@router.post("/{id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services import notifications as svc
    await svc.mark_read(db, user["id"], id)
