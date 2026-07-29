from datetime import datetime, timedelta
from typing import Any

import bcrypt
import hashlib
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
    """SHA-256 hex of the refresh token. Refresh tokens are 64 bytes of CSPRNG
    output — long enough that brute-force is infeasible, so we use a fast hash
    here (vs bcrypt for passwords) so /v1/auth/refresh can look up the row by
    indexed hash in O(1).
    """
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_refresh_token(raw: str) -> str:
    """Return the SHA-256 hex of the presented refresh token. Callers SELECT
    `RefreshToken WHERE token_hash = verify_refresh_token(presented)` and act
    on the result. Returning the hash (rather than a bool) makes the lookup
    a single indexed query without comparing in Python."""
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return str(payload["sub"])


def verify_apple_identity_token(token: str) -> dict:
    """Verify an Apple identity token (Sign in with Apple) and return the
    decoded payload: {"sub": "<stable user id>", "email": "...", "name": "..."}.

    Apple identity tokens are signed JWS with RS256, with public keys served
    from https://appleid.apple.com/auth/keys. Production must:
      1. Fetch JWKS, cache it (1h TTL)
      2. Verify the JWT signature against the matching kid
      3. Verify `aud` == settings.apple_bundle_id
      4. Verify `iss` == "https://appleid.apple.com"
      5. Optionally verify `nonce` matches what mobile sent
    Phase 3 work — for Phase 2 we return a stub error if the token can't be
    verified. Mobile-side Apple Sign-In is dev-only until this is implemented.
    """
    raise NotImplementedError(
        "Apple identity token verification — requires JWKS fetch from appleid.apple.com (Phase 3)"
    )


def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token (Sign in with Google) and return the payload.

    Production flow:
      1. Use google-auth library to verify the JWT
      2. Verify `aud` matches one of our OAuth client IDs
      3. Verify `iss` == "accounts.google.com" or "https://accounts.google.com"
      4. Verify `email_verified` is true
    Phase 3 work — until then, the OAuth router will return 503.
    """
    raise NotImplementedError(
        "Google ID token verification — requires google-auth library + client ID (Phase 3)"
    )
