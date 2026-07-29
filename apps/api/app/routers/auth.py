from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    AppleAuthRequest,
    AuthResponse,
    ForgotRequest,
    GoogleAuthRequest,
    OtpRequest,
    OtpVerifyRequest,
    RefreshRequest,
    ResetRequest,
    SigninRequest,
    SignupRequest,
    SignupResponse,
)
from app.services import auth as auth_service

router = APIRouter()


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.refresh(db, payload)


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_202_ACCEPTED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.signup(db, payload)


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.signin(db, payload)


@router.post("/apple", response_model=AuthResponse)
async def apple(payload: AppleAuthRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.apple(db, payload)


@router.post("/google", response_model=AuthResponse)
async def google(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.google(db, payload)


@router.post("/forgot", status_code=status.HTTP_202_ACCEPTED)
async def forgot(
    payload: ForgotRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.forgot(db, payload)


@router.post("/reset")
async def reset(
    payload: ResetRequest,
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.reset(db, payload)


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
async def otp_request(payload: OtpRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.request_signup_otp(db, payload.email)


@router.post("/otp/resend", status_code=status.HTTP_202_ACCEPTED)
async def otp_resend(payload: OtpRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.request_signup_otp(db, payload.email)


@router.post("/otp/verify", response_model=AuthResponse)
async def otp_verify(payload: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.verify_signup_otp(db, payload.email, payload.code)