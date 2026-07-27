from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    AppleAuthRequest,
    AuthResponse,
    ForgotRequest,
    GoogleAuthRequest,
    RefreshRequest,
    ResetRequest,
    SigninRequest,
    SignupRequest,
)
from app.services import auth as auth_service

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.signup(db, payload)


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.signin(db, payload)


@router.post("/refresh")
async def refresh(payload: RefreshRequest):
    return await auth_service.refresh(payload)


@router.post("/apple", response_model=AuthResponse)
async def apple(payload: AppleAuthRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.apple(db, payload)


@router.post("/google", response_model=AuthResponse)
async def google(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.google(db, payload)


@router.post("/forgot", status_code=status.HTTP_202_ACCEPTED)
async def forgot(payload: ForgotRequest):
    return await auth_service.forgot(payload)


@router.post("/reset")
async def reset(payload: ResetRequest):
    return await auth_service.reset(payload)