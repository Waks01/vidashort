import secrets
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    hash_password,
    verify_password,
    verify_access_token,
    verify_apple_identity_token,
    verify_google_id_token,
)
from app.db.models import User, UserIdentity, RefreshToken, PasswordReset


async def signup(db: AsyncSession, payload) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        raise AppError(status_code=409, code="email_taken", detail="Email already registered")
    user = User(
        id=__import__("uuid").uuid4(),
        email=payload.email.lower(),
        name=payload.name,
        role="viewer",
    )
    db.add(user)
    identity = UserIdentity(
        id=__import__("uuid").uuid4(),
        user_id=user.id,
        provider="email",
        provider_user_id=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(identity)
    await db.flush()
    access = create_access_token(str(user.id), user.role, False)
    refresh_raw = create_refresh_token()
    refresh = RefreshToken(
        id=__import__("uuid").uuid4(),
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_raw),
        expires_at=datetime.utcnow() + timedelta(seconds=settings.refresh_ttl_s),
    )
    db.add(refresh)
    await db.commit()
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "avatarUrl": user.avatar_url,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        },
        "access_token": access,
        "refresh_token": refresh_raw,
    }


async def signin(db: AsyncSession, payload) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError(status_code=400, code="invalid_credentials", detail="Invalid email or password")
    identity = (await db.execute(select(UserIdentity).where(UserIdentity.user_id == user.id, UserIdentity.provider == "email"))).scalar_one_or_none()
    if not identity or not verify_password(payload.password, identity.password_hash):
        raise AppError(status_code=400, code="invalid_credentials", detail="Invalid email or password")
    if user.banned_at:
        raise AppError(status_code=403, code="user_banned", detail="Account banned")
    if user.deleted_at:
        raise AppError(status_code=403, code="user_deleted", detail="Account deleted")
    access = create_access_token(str(user.id), user.role, False)
    refresh_raw = create_refresh_token()
    refresh = RefreshToken(
        id=__import__("uuid").uuid4(),
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_raw),
        expires_at=datetime.utcnow() + timedelta(seconds=settings.refresh_ttl_s),
    )
    db.add(refresh)
    identity.last_login_at = datetime.utcnow()
    db.add(identity)
    await db.commit()
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "avatarUrl": user.avatar_url,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        },
        "access_token": access,
        "refresh_token": refresh_raw,
    }


async def refresh(payload) -> dict:
    raise NotImplementedError("Refresh token rotation not implemented yet")


async def apple(db: AsyncSession, payload) -> dict:
    info = verify_apple_identity_token(payload.identity_token)
    result = await db.execute(select(UserIdentity).where(UserIdentity.provider == "apple", UserIdentity.provider_user_id == info["sub"]))
    identity = result.scalar_one_or_none()
    if not identity:
        user = User(id=__import__("uuid").uuid4(), email=info.get("email", ""), name=payload.name or info.get("email", ""), role="viewer")
        db.add(user)
        identity = UserIdentity(
            id=__import__("uuid").uuid4(),
            user_id=user.id,
            provider="apple",
            provider_user_id=info["sub"],
            email=user.email,
        )
        db.add(identity)
        await db.flush()
    else:
        user = await db.get(User, identity.user_id)
    access = create_access_token(str(user.id), user.role, False)
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "avatarUrl": user.avatar_url,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        },
        "access_token": access,
        "refresh_token": create_refresh_token(),
    }


async def google(db: AsyncSession, payload) -> dict:
    info = verify_google_id_token(payload.id_token)
    result = await db.execute(select(UserIdentity).where(UserIdentity.provider == "google", UserIdentity.provider_user_id == info["sub"]))
    identity = result.scalar_one_or_none()
    if not identity:
        user = User(id=__import__("uuid").uuid4(), email=info.get("email", ""), name=info.get("name", ""), role="viewer")
        db.add(user)
        identity = UserIdentity(
            id=__import__("uuid").uuid4(),
            user_id=user.id,
            provider="google",
            provider_user_id=info["sub"],
            email=user.email,
        )
        db.add(identity)
        await db.flush()
    else:
        user = await db.get(User, identity.user_id)
    access = create_access_token(str(user.id), user.role, False)
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "avatarUrl": user.avatar_url,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        },
        "access_token": access,
        "refresh_token": create_refresh_token(),
    }


async def forgot(db: AsyncSession, payload) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32)
        reset = PasswordReset(
            id=__import__("uuid").uuid4(),
            user_id=user.id,
            token_hash=hash_password(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(reset)
        await db.commit()
        # In production, email the token to the user
    return {"ok": True}


async def reset(db: AsyncSession, payload) -> dict:
    raise NotImplementedError("Password reset not implemented yet")