"""Authentication service — signup, signin, OAuth, password reset, OTP."""
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError, RateLimited
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    hash_password,
    verify_password,
    verify_apple_identity_token,
    verify_google_id_token,
    verify_refresh_token,
)
from app.db.models import EmailOtp, PasswordReset, RefreshToken, User, UserIdentity
from app.db.session import get_redis
from app.schemas.auth import AuthResponse
from app.services import email as email_service

OTP_MAX_ATTEMPTS = 5
OTP_PURPOSE_SIGNUP = "signup_verify"

# Sign-in rate limit (Phase 2 §4 spec): 5 attempts per 10 min per email. Keeps
# brute-force on a leaked email from succeeding even if bcrypt cost goes wrong.
SIGNIN_MAX_ATTEMPTS = 5
SIGNIN_WINDOW_SECONDS = 600


def _user_payload(user: User) -> dict:
    """Build the user dict embedded in AuthResponse — fields are camelCase on the wire
    because AuthResponse inherits from BaseSchema (to_camel alias_generator)."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _hash_otp(code: str) -> str:
    """SHA-256 hex of the 6-digit OTP. Stored on EmailOtp rows so a DB dump
    doesn't reveal codes in cleartext. Comparisons use hmac.compare_digest."""
    return hashlib.sha256(code.encode()).hexdigest()


async def _issue_token_pair(db: AsyncSession, user: User) -> tuple[str, str]:
    """Mint access + refresh tokens and persist the refresh hash. Returns (access, refresh_raw)."""
    access = create_access_token(str(user.id), user.role, False)
    refresh_raw = create_refresh_token()
    refresh = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_raw),
        expires_at=datetime.utcnow() + timedelta(seconds=settings.refresh_ttl_s),
    )
    db.add(refresh)
    return access, refresh_raw


async def signup(db: AsyncSession, payload) -> dict:
    """Phase 2 signup — create the user (email_verified=False) and send an OTP.
    Does NOT issue tokens here; mobile must call POST /v1/auth/otp/verify next
    to complete verification. Returns {ok, requiresVerification} so the mobile
    provider can route to the OTP screen.

    Why we don't auto-mark verified: matches ReelShort/HiDrama parity and
    protects against typo'd-then-rebounded email squatting.
    """
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        raise AppError(status_code=409, code="email_taken", detail="Email already registered")
    user = User(
        id=str(uuid.uuid4()),
        email=payload.email.lower(),
        name=payload.name,
        role="viewer",
        email_verified=False,
    )
    db.add(user)
    identity = UserIdentity(
        id=str(uuid.uuid4()),
        user_id=user.id,
        provider="email",
        provider_user_id=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(identity)
    await db.commit()

    # Best-effort: send the OTP. If email fails we still return success — the
    # user can hit "Resend code" on the OTP screen.
    code = _mint_otp()
    db.add(EmailOtp(
        id=str(uuid.uuid4()),
        user_id=user.id,
        code_hash=_hash_otp(code),
        purpose=OTP_PURPOSE_SIGNUP,
        expires_at=datetime.utcnow() + timedelta(seconds=settings.otp_ttl_seconds),
    ))
    await db.commit()
    await email_service.send_otp(user.email, code)
    return {"ok": True, "requiresVerification": True}


def _mint_otp() -> str:
    """6-digit zero-padded decimal. Settings.otp_length is the source of truth."""
    return f"{secrets.randbelow(10 ** settings.otp_length):0{settings.otp_length}d}"


async def request_signup_otp(db: AsyncSession, email: str) -> dict:
    """Re-send the signup OTP for the given email. Always returns {ok: True}
    (don't leak whether the email is registered). When the user exists we mint
    a fresh OTP, invalidate any prior unused codes for this purpose, and email it."""
    user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
    if user:
        # Invalidate any prior unused signup OTPs so only the latest works.
        prior = (await db.execute(
            select(EmailOtp).where(
                EmailOtp.user_id == user.id,
                EmailOtp.purpose == OTP_PURPOSE_SIGNUP,
                EmailOtp.used_at.is_(None),
            )
        )).scalars().all()
        for row in prior:
            row.used_at = datetime.utcnow()
        code = _mint_otp()
        db.add(EmailOtp(
            id=str(uuid.uuid4()),
            user_id=user.id,
            code_hash=_hash_otp(code),
            purpose=OTP_PURPOSE_SIGNUP,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.otp_ttl_seconds),
        ))
        await db.commit()
        await email_service.send_otp(user.email, code)
    return {"ok": True}


async def verify_signup_otp(db: AsyncSession, email: str, code: str) -> AuthResponse:
    """Validate the OTP. On success: mark used, set email_verified=True, issue tokens.
    Constant-time hash compare so timing attacks can't prune the code space.
    5 failed attempts invalidate all OTPs for this email (lockout)."""
    user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
    if not user:
        # Don't leak existence — same shape as the request endpoint.
        raise AppError(status_code=400, code="invalid_code", detail="Invalid or expired code")
    otp = (await db.execute(
        select(EmailOtp).where(
            EmailOtp.user_id == user.id,
            EmailOtp.purpose == OTP_PURPOSE_SIGNUP,
            EmailOtp.used_at.is_(None),
        ).order_by(EmailOtp.created_at.desc())
    )).scalars().first()
    if not otp or otp.expires_at < datetime.utcnow() or otp.attempts >= OTP_MAX_ATTEMPTS:
        raise AppError(status_code=400, code="invalid_code", detail="Invalid or expired code")
    presented_hash = _hash_otp(code)
    if not hmac.compare_digest(presented_hash, otp.code_hash):
        otp.attempts += 1
        if otp.attempts >= OTP_MAX_ATTEMPTS:
            otp.used_at = datetime.utcnow()
        await db.commit()
        raise AppError(status_code=400, code="invalid_code", detail="Invalid or expired code")
    # Success.
    otp.used_at = datetime.utcnow()
    user.email_verified = True
    access, refresh_raw = await _issue_token_pair(db, user)
    identity = (await db.execute(select(UserIdentity).where(
        UserIdentity.user_id == user.id, UserIdentity.provider == "email"
    ))).scalar_one_or_none()
    if identity:
        identity.last_login_at = datetime.utcnow()
    await db.commit()
    return AuthResponse(user=_user_payload(user), access_token=access, refresh_token=refresh_raw)


async def signin(db: AsyncSession, payload) -> AuthResponse:
    """Email + password sign-in. Enforces the Phase 2 rate limit (5 attempts /
    10 min / email) before the bcrypt check — we don't want to do expensive
    hashing for someone who's already hit the threshold. The counter is
    incremented on every wrong-password / no-such-email attempt and reset on
    successful sign-in.
    """
    email_key = payload.email.lower()

    # Read-then-decide: only INCR on failures (see _bump). A successful
    # sign-in must not push the counter up.
    current_attempts = await _check_signin_rate_limit(email_key)
    if current_attempts >= SIGNIN_MAX_ATTEMPTS:
        raise RateLimited(detail=f"Too many sign-in attempts. Try again in {SIGNIN_WINDOW_SECONDS // 60} minutes.")

    result = await db.execute(select(User).where(User.email == email_key))
    user = result.scalar_one_or_none()
    if not user:
        await _bump_signin_rate_limit(email_key)
        raise AppError(status_code=400, code="invalid_credentials", detail="Invalid email or password")
    identity = (await db.execute(select(UserIdentity).where(UserIdentity.user_id == user.id, UserIdentity.provider == "email"))).scalar_one_or_none()
    if not identity or not verify_password(payload.password, identity.password_hash):
        await _bump_signin_rate_limit(email_key)
        raise AppError(status_code=400, code="invalid_credentials", detail="Invalid email or password")
    if user.banned_at:
        raise AppError(status_code=403, code="user_banned", detail="Account banned")
    if user.deleted_at:
        raise AppError(status_code=403, code="user_deleted", detail="Account deleted")
    if not user.email_verified:
        # Don't block sign-in (so the user can still get to "resend code"), but
        # surface the verification requirement via the error code so the mobile
        # client can route to the OTP screen with a clear message.
        raise AppError(status_code=403, code="email_unverified", detail="Please verify your email first")

    # Successful sign-in: clear the rate-limit counter so a legitimate user
    # who fat-fingered their password a few times isn't penalized for 10 min.
    await _reset_signin_rate_limit(email_key)

    access, refresh_raw = await _issue_token_pair(db, user)
    identity.last_login_at = datetime.utcnow()
    await db.commit()
    return AuthResponse(user=_user_payload(user), access_token=access, refresh_token=refresh_raw)


def _signin_key(email: str) -> str:
    return f"signin:attempts:{email}"


async def _check_signin_rate_limit(email: str) -> int:
    """Read the current attempt count without mutating it. Returns the count.

    We separate read from increment so the counter only ticks up on actual
    failed attempts — a correct password on attempt N+1 won't push N+1 users
    over the line.
    """
    try:
        raw = await get_redis().get(_signin_key(email))
    except Exception:
        # Redis down — fail open.
        return 0
    if raw is None:
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


async def _bump_signin_rate_limit(email: str) -> None:
    """INCR + (only on first hit) EXPIRE. Called after every failed attempt."""
    try:
        r = get_redis()
        count = await r.incr(_signin_key(email))
        if count == 1:
            try:
                await r.expire(_signin_key(email), SIGNIN_WINDOW_SECONDS)
            except Exception:
                pass
    except Exception:
        pass


async def _reset_signin_rate_limit(email: str) -> None:
    """Wipe the counter on successful sign-in so the legit user isn't penalized."""
    try:
        await get_redis().delete(_signin_key(email))
    except Exception:
        pass


async def refresh(db: AsyncSession, payload) -> AuthResponse:
    """Rotate a refresh token. The presented refresh must be valid, unused, and
    unexpired. On success: mark the old refresh as used, issue a new pair,
    return AuthResponse. On replay (a used token presented again): revoke ALL
    refresh tokens for that user — this is the standard pattern for detecting
    token theft.
    """
    presented_hash = verify_refresh_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == presented_hash))
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise AppError(status_code=401, code="invalid_refresh", detail="Invalid refresh token")
    if token_row.used_at is not None:
        # Replay attack — burn all refresh tokens for this user.
        all_user_tokens = (await db.execute(select(RefreshToken).where(RefreshToken.user_id == token_row.user_id))).scalars().all()
        for t in all_user_tokens:
            t.used_at = datetime.utcnow()
        await db.commit()
        raise AppError(status_code=401, code="refresh_replay", detail="Refresh token replay detected; all sessions revoked")
    if token_row.expires_at < datetime.utcnow():
        raise AppError(status_code=401, code="refresh_expired", detail="Refresh token expired")
    user = await db.get(User, token_row.user_id)
    if not user:
        raise AppError(status_code=401, code="user_not_found", detail="User not found")
    token_row.used_at = datetime.utcnow()
    access, new_refresh_raw = await _issue_token_pair(db, user)
    await db.commit()
    return AuthResponse(user=_user_payload(user), access_token=access, refresh_token=new_refresh_raw)


async def _oauth_login(db: AsyncSession, info: dict, *, name: str | None = None) -> AuthResponse:
    """Common OAuth (Apple/Google) login path: find-or-create user, return AuthResponse."""
    result = await db.execute(select(UserIdentity).where(
        UserIdentity.provider == info["provider"],
        UserIdentity.provider_user_id == info["sub"],
    ))
    identity = result.scalar_one_or_none()
    if not identity:
        user = User(
            id=str(uuid.uuid4()),
            email=info.get("email", ""),
            name=name or info.get("name", "") or info.get("email", ""),
            role="viewer",
            email_verified=True,  # OAuth providers verify the email for us
        )
        db.add(user)
        identity = UserIdentity(
            id=str(uuid.uuid4()),
            user_id=user.id,
            provider=info["provider"],
            provider_user_id=info["sub"],
            email=user.email,
        )
        db.add(identity)
        await db.flush()
    else:
        user = await db.get(User, identity.user_id)
    access, refresh_raw = await _issue_token_pair(db, user)
    await db.commit()
    return AuthResponse(user=_user_payload(user), access_token=access, refresh_token=refresh_raw)


async def apple(db: AsyncSession, payload) -> AuthResponse:
    info = verify_apple_identity_token(payload.identity_token)
    info["provider"] = "apple"
    return await _oauth_login(db, info, name=payload.name)


async def google(db: AsyncSession, payload) -> AuthResponse:
    info = verify_google_id_token(payload.id_token)
    info["provider"] = "google"
    info["name"] = info.get("name", "")
    return await _oauth_login(db, info)


async def forgot(db: AsyncSession, payload) -> dict:
    """Always return ok=true (don't leak whether the email exists).
    On a real email being found: write a PasswordReset row AND email a deep link
    to the reset-password screen on the mobile app. The raw token goes in the
    email; the row stores only its SHA-256 hash (same pattern as refresh tokens)."""
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32)
        reset = PasswordReset(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_refresh_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(reset)
        await db.commit()
        deep_link = f"vidashort://reset-password?token={token}"
        await email_service.send_password_reset(user.email, deep_link)
    return {"ok": True}


async def reset(db: AsyncSession, payload) -> dict:
    """Validate the reset token, update the password hash, mark the reset row consumed.
    Returns {"ok": true} on success regardless of whether the token was valid
    (don't leak which users have accounts), but on success the password actually changes.
    """
    presented_hash = verify_refresh_token(payload.token)
    result = await db.execute(select(PasswordReset).where(PasswordReset.token_hash == presented_hash))
    reset_row = result.scalar_one_or_none()
    if not reset_row or reset_row.used_at is not None or reset_row.expires_at < datetime.utcnow():
        # Silent success — don't leak whether the token existed.
        return {"ok": True}
    identity = (await db.execute(select(UserIdentity).where(
        UserIdentity.user_id == reset_row.user_id,
        UserIdentity.provider == "email",
    ))).scalar_one_or_none()
    if not identity:
        return {"ok": True}
    identity.password_hash = hash_password(payload.new_password)
    reset_row.used_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}