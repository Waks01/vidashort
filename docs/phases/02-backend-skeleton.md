# Phase 2 — FastAPI backend skeleton

## Goal

A FastAPI service running on Fly.io that handles sign-up, sign-in, refresh, and `GET /v1/me`. End-to-end with a real Postgres (Neon) + Redis (Upstash). The mobile app (Phase 1) flips its API base URL and starts using the real backend instead of the mock.

## Why this order

Before we wire up IAP, ads, or content delivery, we need the spine:
- A real database with real users.
- Real auth with real tokens.
- A real `/v1/me` that the mobile app can poll on launch.

Everything else (coins, ads, content) builds on this.

## What's in scope

### 1. Backend tree (Day 1)

- `apps/api/` with the full tree from `docs/backend/00-tree.md`.
- `pyproject.toml` with pinned deps (FastAPI, SQLAlchemy 2, Pydantic v2, alembic, asyncpg, redis, python-jose, passlib, httpx, structlog, sentry-sdk).
- `docker-compose.yml` for local Postgres + Redis.
- `.env.example` with every env var.
- `app/main.py` with the FastAPI() instance, CORS, lifespan (DB + Redis init/teardown), Sentry, structlog.

### 2. Core (Day 1-2)

- `app/core/config.py` — Pydantic Settings.
- `app/core/security.py` — bcrypt, JWT encode/decode, password hashing.
- `app/core/deps.py` — `get_db`, `get_redis`, `get_current_user`, `get_creator`, `get_admin`.
- `app/core/errors.py` — `PaywallRequired`, `InsufficientCoins`, `AdCapReached`, `VipRequired`, `NotFound`, `RateLimited`. Each has a handler that returns the canonical error envelope.
- `app/core/logging.py` — structlog config, request-id propagation.

### 3. Database (Day 2)

- `app/db/base.py` — SQLAlchemy 2 declarative base.
- `app/db/session.py` — async engine, `SessionLocal`.
- `app/db/models/user.py` — `User` model.
- `app/db/models/identity.py` — `UserIdentity` model.
- `app/db/models/refresh_token.py` — `RefreshToken` model.
- `migrations/env.py` — Alembic env, async engine.
- `migrations/versions/0001_initial_users.py` — the 3 tables + indexes.

### 4. Auth router (Day 3)

- `app/schemas/auth.py` — request/response shapes.
- `app/routers/auth.py` — `/v1/auth/signup`, `/v1/auth/signin`, `/v1/auth/refresh`, `/v1/auth/forgot`, `/v1/auth/reset`. Apple + Google in Phase 2.5.
- Token generation, refresh rotation, rate limiting (5 signin attempts / 10 min / user).

### 5. Me router (Day 3)

- `app/schemas/user.py` — `User`, `MeResponse`.
- `app/routers/me.py` — `GET /v1/me`, `PATCH /v1/me`, `POST /v1/me/age-confirm`, `DELETE /v1/me`.
- The mobile app polls this on launch.

### 6. Provisioning (Day 4)

- Fly.io app: `vidashort-api-staging` (no deploy yet, just `fly launch --no-deploy`).
- Neon project: `vidashort-staging` (free tier, 0.5 GB).
- Upstash Redis: `vidashort-staging` (free tier).
- All creds in `.env` per-developer.
- Local docker-compose validated.

### 7. Tests (Day 4-5)

- `tests/conftest.py` — fixtures: test client, DB session (per-test rollback), Redis, signed user.
- `tests/test_auth.py` — signup, signin, refresh, refresh-replay-revokes, rate-limit.
- `tests/test_me.py` — me, update, age-confirm, delete.
- `tests/test_health.py` — `/health` returns 200 with DB + Redis ping.

### 8. Mobile flip (Day 5)

- Mobile `lib/api/` swaps the mock implementation for the real client (just import the `real/` folder instead of `mock/`).
- Mobile `EXPO_PUBLIC_API_URL=https://staging-api.vidashort.app/v1` (or localhost for dev).
- The visual prototype (`apps/design/`) is **not** wired to the real API. It stays on localStorage mocks.

## What's out of scope

- ❌ Content / catalog (Phase 2.5).
- ❌ Paywall / entitlement (Phase 3).
- ❌ Coins / IAP (Phase 3).
- ❌ Ads (Phase 3).
- ❌ Creator + admin (Phase 3).
- ❌ Apple + Google sign-in (Phase 2.5).
- ❌ Webhooks (Phase 3, when we add RevenueCat).
- ❌ TMDB / Cloudflare (Phase 2.5).
- ❌ Push notifications (Phase 4).
- ❌ Production deploy (Phase 1.5 has the EAS side; Phase 5 has the API prod side).

## Tasks (ordered, with line estimates)

1. **Backend skeleton** — directory tree, `pyproject.toml`, `docker-compose.yml`, `.env.example`, `app/main.py`. **~ 200 lines.**
2. **Config + security + deps** — `core/*.py`. **~ 400 lines.**
3. **DB base + session + 3 models** — `db/*`. **~ 300 lines.**
4. **Alembic init + first migration** — `migrations/*`. **~ 200 lines.**
5. **Errors + handlers** — `core/errors.py` + exception handlers in `main.py`. **~ 200 lines.**
6. **Auth schemas + router** — `schemas/auth.py`, `routers/auth.py`. **~ 400 lines.**
7. **User schemas + me router** — `schemas/user.py`, `routers/me.py`. **~ 300 lines.**
8. **Tests** — `tests/*`. **~ 600 lines.**
9. **Provisioning** — Neon, Upstash, Fly.io. **0 lines of code, ~ 30 min of clicking.**
10. **Mobile flip** — swap `mock/` for `real/` in `lib/api/index.ts`. **~ 50 lines.**
11. **CORS + smoke test** — verify mobile can sign up against staging. **~ 50 lines.**

Total: **~ 2,700 lines of new Python + ~ 50 lines of TS.**

## Verification

```bash
# Local
cd apps/api
docker-compose up -d  # Postgres + Redis
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# In another terminal:
curl -X POST http://localhost:8000/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"correct-horse-battery","name":"Test","acceptedTerms":true}'
# → 201 with user, accessToken, refreshToken
```

```bash
# Tests
cd apps/api
uv run pytest
# All pass.
```

```bash
# Mobile against staging
# (in apps/mobile/.env)
EXPO_PUBLIC_ENV=staging
EXPO_PUBLIC_API_URL=https://staging-api.vidashort.app/v1
npm run start
# In the iOS simulator: sign up. Watch the API logs. The user row appears in Neon.
```

**Pass criteria:**
- All pytest tests pass (`uv run pytest`).
- The signup → /v1/me flow works end-to-end from a real device (or simulator) against the staging URL.
- No Sentry errors in the first 100 signups.
- The local docker-compose Postgres + Redis work for dev.

## Hand-off

What Phase 2.5 (real auth + content) assumes:
- Auth + /me endpoints are live and tested.
- Migrations run cleanly on Neon.
- The mobile app can talk to staging without code changes.
- The token storage in secure-store is in place.
- The 401 → refresh → retry flow works.

What Phase 1.5 (build) assumes:
- The API has a stable staging URL.
- CORS is set up for the mobile app's origin (in dev, `*` is fine).
