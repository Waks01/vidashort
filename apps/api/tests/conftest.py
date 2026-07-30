"""Pytest fixtures for the vidashort API.

Wiring notes
------------
The FastAPI app (`app.main:app`) uses `app.db.session.get_db` to open sessions
on the *global* engine built from `settings.database_url`. For tests we
spin up a separate in-memory SQLite engine (via aiosqlite), bind it to a
fresh `SessionLocal`, and override `get_db` on the app with `app.dependency_overrides`.

We also inject test env vars BEFORE `Settings()` is imported anywhere, since
Pydantic-settings reads env at class-definition time.
"""
import asyncio
import os
from typing import AsyncGenerator

# Test env must be set BEFORE `app.*` is imported (Settings() reads env at
# module-import time). Skip if already set by an outer harness.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-prod-please")
os.environ.setdefault("CF_STREAM_SIGNING_KEY", "test-cf-key")
os.environ.setdefault("REVENUECAT_WEBHOOK_SECRET", "test-rc-key")
os.environ.setdefault("APPLE_PRIVATE_KEY", "test-apple-key")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", "test-google-key")
# Force RESEND_API_KEY to empty so the email service takes the no-op dev branch
# (logs the OTP / deep link). The test capture hooks below still observe calls.
os.environ.setdefault("RESEND_API_KEY", "")
os.environ.setdefault("RESEND_EMAIL_FROM", "test@vidashort.app")
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("POSTHOG_API_KEY", "")
os.environ.setdefault("POSTHOG_HOST", "")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.db import session as session_module
from app.db.models import (  # noqa: F401 — register all mappers on Base.metadata
    AdImpression, AuditLog, CoinTxn, Comment, CreatorEarning, EmailOtp, Episode,
    Favorite, ModerationItem, PasswordReset, PayoutRequest, RefreshToken,
    Series, User, UserIdentity, VipEntitlement, WatchHistory,
)
from app.main import app
from app.services import email as email_service


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Fresh in-memory SQLite engine per test — guarantees isolation."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session


class _FakeRedis:
    """In-process Redis stand-in for tests. Implements the minimal surface the
    auth rate-limit + health endpoint actually call: ``incr``, ``expire``,
    ``delete``, ``ping``. Keeps everything in a plain dict so each test gets
    a fresh client (autouse fixture below wipes state per test).

    Why not fakeredis: avoiding a new dependency per CLAUDE.md §7 — every
    command the production code path runs is also exercised here, just
    against an in-memory dict instead of a real Redis server.
    """

    def __init__(self) -> None:
        self.store: dict[str, tuple[int, float | None]] = {}
        self.up: bool = True

    async def ping(self) -> bool:
        if not self.up:
            raise ConnectionError("fake redis down")
        return True

    async def get(self, key: str) -> str | None:
        v, _ = self.store.get(key, (None, None))
        return None if v is None else str(v)

    async def incr(self, key: str) -> int:
        # INCR creates the key at 1 if missing — see https://redis.io/commands/incr
        v, _ = self.store.get(key, (0, None))
        v += 1
        self.store[key] = (v, self.store.get(key, (0, None))[1])
        return v

    async def expire(self, key: str, seconds: int) -> bool:
        # EXPIRE returns 1 if the key existed, 0 otherwise.
        if key not in self.store:
            return False
        v, _ = self.store[key]
        self.store[key] = (v, seconds)
        return True

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.store[key] = (value, ex)
        return True

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    async def delete(self, *keys: str) -> int:
        removed = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                removed += 1
        return removed

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        if key not in self.store:
            return 0
        v, _ = self.store[key]
        if not isinstance(v, dict):
            return 0
        to_remove = [m for m, s in v.items() if s < min_score or s > max_score]
        for m in to_remove:
            del v[m]
        return len(to_remove)

    async def zcard(self, key: str) -> int:
        if key not in self.store:
            return 0
        v, _ = self.store[key]
        if isinstance(v, dict):
            return len(v)
        return 1

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        if key not in self.store:
            self.store[key] = ({}, None)
        v, _ = self.store[key]
        if not isinstance(v, dict):
            v = {}
            self.store[key] = (v, self.store[key][1])
        for member, score in mapping.items():
            v[member] = score
        return len(mapping)

    async def zrem(self, key: str, *members: str) -> int:
        if key not in self.store:
            return 0
        v, _ = self.store[key]
        if not isinstance(v, dict):
            return 0
        removed = 0
        for m in members:
            if m in v:
                del v[m]
                removed += 1
        return removed

    def reset(self) -> None:
        self.store.clear()
        self.up = True


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch) -> _FakeRedis:
    """Per-test in-memory Redis. Autouse so tests that don't care about Redis
    still get a no-op ping (so /health passes) and tests that exercise the
    rate limiter get isolation between cases.

    Patches every consumer's captured reference to `get_redis` — at import
    time, each module captures its own reference to the function object, so
    setting `app.db.session.get_redis` doesn't update the others. Every
    consumer needs its own patch.
    """
    fake = _FakeRedis()
    import app.core.deps as deps_module
    import app.main as main_module
    import app.routers.webhooks as webhooks_module
    import app.services.ad_cap as ad_cap_module
    import app.services.auth as auth_service_module
    import app.core.rate_limit as rate_limit_module
    monkeypatch.setattr(session_module, "get_redis", lambda: fake)
    monkeypatch.setattr(deps_module, "get_redis", lambda: fake)
    monkeypatch.setattr(main_module, "get_redis", lambda: fake)
    monkeypatch.setattr(ad_cap_module, "get_redis", lambda: fake)
    monkeypatch.setattr(webhooks_module, "get_redis", lambda: fake)
    monkeypatch.setattr(auth_service_module, "get_redis", lambda: fake)
    monkeypatch.setattr(rate_limit_module, "get_redis", lambda: fake)
    yield fake
    fake.reset()


@pytest_asyncio.fixture
async def client(engine):
    """HTTP test client + override `get_db` to use the per-test engine.

    Every test gets a fresh engine (see above), so tables are empty unless
    the test seeds them via `db_session` or HTTP calls.
    """
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[session_module.get_db] = _override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


def make_token(user_id: str, role: str = "viewer", vip: bool = False) -> str:
    """Mint a real access JWT for tests (same path the server uses)."""
    from datetime import datetime, timedelta
    from jose import jwt
    payload = {
        "sub": user_id,
        "email": "",
        "role": role,
        "vip": vip,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": datetime.utcnow() + timedelta(seconds=settings.access_ttl_s),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def auth_headers(user_id: str, role: str = "viewer", vip: bool = False) -> dict:
    return {"Authorization": f"Bearer {make_token(user_id, role, vip)}"}


class _EmailCapture:
    """Records every (to, subject, code_or_link) tuple the email service is
    asked to send. Tests assert on this instead of mocking httpx — the auth
    service uses our `email_service` module directly, so swapping its
    `send_otp` / `send_password_reset` functions captures everything cleanly.

    The current capture is exposed via the module-level `_current` slot so
    helper functions (signup_and_verify, etc.) can read the latest OTP code
    without threading the cap object through every test call site.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.otp_calls: list[dict] = []
        self.reset_calls: list[dict] = []

    async def send_otp(self, to: str, code: str) -> bool:
        self.otp_calls.append({"to": to, "code": code})
        _current_capture = self  # noqa: F841 — referenced by external helpers
        return True

    async def send_password_reset(self, to: str, deep_link: str) -> bool:
        self.reset_calls.append({"to": to, "deep_link": deep_link})
        return True


# Module-level pointer to the active capture. Set by the autouse fixture
# before each test; read by `signup_and_verify` to find the OTP code.
_current_capture: _EmailCapture | None = None


def _current() -> _EmailCapture:
    if _current_capture is None:
        raise RuntimeError("No email capture bound — autouse fixture did not run")
    return _current_capture


@pytest.fixture(autouse=True)
def email_capture(monkeypatch) -> _EmailCapture:
    """Patch the email_service module's two outbound functions with capture
    shims for every test (autouse). Tests that want to inspect what was sent
    just request this fixture by name and read `cap.otp_calls` /
    `cap.reset_calls`. Tests that don't care get a silent no-op capture so
    nothing leaks to the dev-log branch or to real Resend."""
    global _current_capture
    cap = _EmailCapture()
    _current_capture = cap
    monkeypatch.setattr(email_service, "send_otp", cap.send_otp)
    monkeypatch.setattr(email_service, "send_password_reset", cap.send_password_reset)
    yield cap
    _current_capture = None


async def signup_and_verify(client, *, email: str, password: str, name: str = "Test User") -> dict:
    """Sign up a user through the OTP-gated flow and return the AuthResponse.

    Tests that need a verified user call this. The autouse `email_capture`
    fixture captures the OTP code at signup time; we read the latest one here.
    """
    await client.post("/v1/auth/signup", json={"email": email, "password": password, "name": name})
    cap = _current()
    assert cap.otp_calls, "signup did not call send_otp — fixture broken?"
    code = cap.otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()