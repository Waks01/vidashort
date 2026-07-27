from datetime import datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, role: str, vip: bool = False, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=settings.access_ttl_s))
    payload = {
        "sub": str(user_id),
        "email": "",
        "role": role,
        "vip": vip,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token() -> str:
    import secrets

    return secrets.token_urlsafe(64)


def hash_refresh_token(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return str(payload["sub"])


def verify_apple_identity_token(token: str) -> dict:
    raise NotImplementedError("Apple identity token verification not implemented")


def verify_google_id_token(token: str) -> dict:
    raise NotImplementedError("Google ID token verification not implemented")
