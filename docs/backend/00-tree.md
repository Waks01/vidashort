# Backend tree — apps/api/

FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic. Python 3.12. The user creates this in Phase 2.

## Layout

```
apps/api/
├── pyproject.toml
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml          # local Postgres + Redis
├── app/
│   ├── main.py                 # FastAPI() + include_router + CORS + lifespan
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings: env vars
│   │   ├── security.py         # bcrypt, JWT encode/decode
│   │   ├── deps.py             # get_db, get_current_user, get_admin, get_redis
│   │   ├── errors.py           # exception classes + handlers
│   │   └── logging.py          # structlog config
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy declarative base
│   │   ├── session.py          # async engine + SessionLocal
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── identity.py
│   │       ├── content.py      # Series, Episode, SeriesTag
│   │       ├── engagement.py   # WatchHistory, Favorite, Comment
│   │       ├── economy.py      # CoinTxn, CreatorEarning, PayoutRequest, AdImpression
│   │       ├── subscription.py # VIPEntitlement
│   │       └── moderation.py   # ModerationItem, AuditLog
│   ├── schemas/                # Pydantic DTOs, one per domain
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── content.py
│   │   ├── entitlement.py
│   │   ├── coins.py
│   │   ├── ads.py
│   │   ├── creator.py
│   │   └── admin.py
│   ├── routers/                # thin: parse → call service → return schema
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── me.py
│   │   ├── content.py
│   │   ├── entitlement.py
│   │   ├── coins.py
│   │   ├── ads.py
│   │   ├── creator.py
│   │   ├── admin.py
│   │   └── webhooks.py
│   ├── services/               # pure business logic, no HTTP coupling
│   │   ├── __init__.py
│   │   ├── paywall.py
│   │   ├── ad_cap.py
│   │   ├── coins.py
│   │   ├── revenue_split.py
│   │   ├── tmdb.py
│   │   ├── moderation.py
│   │   ├── recommendations.py
│   │   └── revenuecat.py       # webhook signature + sync
│   └── integrations/           # external systems
│       ├── __init__.py
│       ├── cloudflare_stream.py
│       ├── revenuecat.py
│       ├── apple.py
│       ├── google.py
│       ├── tmdb.py
│       └── applovin.py         # S2S callback verify
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures: test client, db, redis, auth
│   ├── test_auth.py
│   ├── test_content.py
│   ├── test_entitlement.py     # the paywall decision tree
│   ├── test_coins.py
│   ├── test_ads.py
│   ├── test_creator.py
│   ├── test_admin.py
│   └── test_webhooks.py
├── migrations/                 # alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_initial.py
│       └── ...
└── scripts/
    ├── seed.py                 # seed dev data (mirrors MockData)
    ├── create_admin.py         # CLI: create an admin user
    └── reset_local.py          # drop + re-migrate + re-seed
```

## Layering rules

- **routers/** are thin: parse the request, call a service, return the response. **No business logic in routers.** No DB queries that aren't `db.query(Model).filter(...)` lookups for ID resolution.
- **services/** own business logic. They take a `db: AsyncSession` and a typed input, return a typed output. They can call other services. They can call integrations. They never touch `request` or `response` objects.
- **integrations/** are pure HTTP / SDK wrappers. They expose typed functions (`mint_signed_playback_url(uid) -> str`). They take config from `core.config`. They never touch the DB.
- **db/models/** are SQLAlchemy 2 declarative. They don't have methods (no `User.signin()`); logic goes in services.
- **schemas/** are Pydantic v2 DTOs. `Model` is for the DB, `Schema` is for the wire. **No `ModelOut` returned directly from a route — always wrap in a Schema.**

## Why this shape

- Routers stay testable by hand (no complex setup).
- Services are testable with just a DB session.
- Integrations are testable with a mock HTTP server.
- The same `paywall.decide()` can later be called from a worker (e.g. a scheduled promo email) without dragging in FastAPI.
- Swapping Cloudflare for Bunny CDN is one file change in `integrations/`, no router changes.

## Database schema (key tables)

See `docs/backend/10-schema.md` for the full DDL and indexes.

The hot tables:

| Table | Purpose | Writes/sec (Phase 1) |
|---|---|---|
| `users` | Account | 1 |
| `series` | Series metadata | 1 |
| `episodes` | Episode metadata | 5 |
| `coin_txn` | Append-only ledger | 100 (read-heavy) |
| `watch_history` | Resume + dedup | 1000 (very write-heavy) |
| `ad_impressions` | Per rewarded ad | 100 |
| `comments` | Episode comments | 10 |
| `favorites` | User → series | 1 |
| `creator_earnings` | 60% credit | 100 |
| `payout_requests` | Cashouts | 0.1 |
| `vip_entitlements` | VIP windows | 1 |
| `moderation_items` | Queue | 1 |
| `audit_log` | Admin actions | 1 |

## Where the paywall lives

`apps/api/app/services/paywall.py` is the single most important file in the codebase. It contains:

```python
async def decide(db: AsyncSession, user: User, episode: Episode) -> PaywallDecision:
    """VIP → free → coins → ad → premium. Order is sacred."""
    if is_vip(db, user):
        return PaywallDecision(path="vip", cost_coins=0, ...)
    if episode.is_free or episode.number <= episode.series.free_episodes:
        return PaywallDecision(path="vip", cost_coins=0, ...)  # semantically free
    if user.coins >= ECONOMY.episode_cost_coins:
        return PaywallDecision(path="coins", cost_coins=ECONOMY.episode_cost_coins, ...)
    if ad_cap_remaining(db, user) > 0:
        return PaywallDecision(path="ad", cost_coins=0, reward_coins=ECONOMY.ad_reward_coins, remaining_ads=ad_cap_remaining(db, user), ...)
    return PaywallDecision(path="premium", cost_coins=0, label="Go VIP to keep watching", ...)


async def pay_with_coins(db: AsyncSession, user: User, episode: Episode) -> UnlockResult:
    """Debit 25 coins, credit 15 to creator (60%), return stream URL."""
    async with db.begin():  # SERIALIZABLE row lock on user
        if user.coins < ECONOMY.episode_cost_coins:
            raise InsufficientCoins()
        user.coins -= ECONOMY.episode_cost_coins
        coin_txn = CoinTxn(user_id=user.id, delta=-ECONOMY.episode_cost_coins,
                            reason="unlock", ref_id=episode.id, balance_after=user.coins)
        db.add(coin_txn)

        if episode.series.creator_id and episode.series.creator_id != user.id:
            creator = await db.get(User, episode.series.creator_id)
            creator_coins = ECONOMY.episode_cost_coins * ECONOMY.revenue_split.creator  # 15
            creator.loyalty_coins += creator_coins
            earning = CreatorEarning(creator_id=creator.id, episode_id=episode.id,
                                      gross_coins=ECONOMY.episode_cost_coins,
                                      creator_coins=creator_coins)
            db.add(earning)

    stream_url = await mint_signed_playback_url(episode.video_uid)
    return UnlockResult(ok=True, source="coins", coins_after=user.coins,
                       creator_credited_coins=creator_coins, playback_url=stream_url)
```

Every test in `tests/test_entitlement.py` exercises a path through this function. If the path doesn't pass, no release.

## Authentication

`apps/api/app/core/security.py` exports:

```python
def create_access_token(user: User) -> str: ...
def create_refresh_token() -> str: ...     # returns raw, also stores hash
def hash_refresh_token(raw: str) -> str: ...
def verify_access_token(token: str) -> UserId: ...
def verify_apple_identity_token(token: str) -> AppleUserInfo: ...
def verify_google_id_token(token: str) -> GoogleUserInfo: ...
def hash_password(plain: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...
```

`core/deps.py` exports:

```python
async def get_db() -> AsyncIterator[AsyncSession]: ...
async def get_redis() -> Redis: ...
async def get_current_user(token: Annotated[str, Depends(bearer)]) -> User: ...
async def get_creator(user: Annotated[User, Depends(get_current_user)]) -> User: ...  # asserts role
async def get_admin(user: Annotated[User, Depends(get_current_user)]) -> User: ...  # asserts role
```

## Configuration

`apps/api/app/core/config.py`:

```python
class Settings(BaseSettings):
    env: Literal["dev", "staging", "prod"] = "dev"
    database_url: str                          # postgresql+asyncpg://...
    redis_url: str                              # redis://...
    jwt_secret: str                             # 32 bytes
    jwt_algorithm: str = "HS256"
    access_ttl_s: int = 3600
    refresh_ttl_s: int = 30 * 86400
    cors_origins: list[str] = ["*"]
    cf_account_id: str
    cf_stream_signing_key: str
    cf_r2_bucket: str
    apple_bundle_id: str
    apple_key_id: str
    apple_team_id: str
    apple_private_key: str                     # PEM
    google_service_account_json: str            # base64-encoded JSON
    revenuecat_webhook_secret: str
    revenuecat_api_key: str
    tmdb_api_key: str | None = None             # not required in dev
    sentry_dsn: str | None = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

`.env.example`:

```bash
ENV=dev
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vidashort
REDIS_URL=redis://localhost:6379
JWT_SECRET=change-me-to-32-random-bytes
# ... etc
```

## Why SQLAlchemy 2 async, not sync

- Async matches FastAPI's async handlers, no thread pool overhead.
- `asyncpg` is 2-3× faster than psycopg2.
- Migrations are still sync (Alembic doesn't support async migrations cleanly; run with a sync engine in `migrations/env.py`).

## Why Pydantic v2, not dataclasses

- Pydantic v2 is Rust-backed, very fast.
- Schema validation, serialisation, OpenAPI generation — one tool.
- v1 had a lot of gotchas around `Config` and `validator`. v2 is cleaner.

## Why no ORM magic in routers

- Explicit `db.add()`, `db.commit()`, `db.refresh()` is verbose but obvious.
- We can read a router and know exactly what hits the DB.
- Audit log writes are explicit (we don't use SQLAlchemy events for this — too magical).

## Why `services/` are not classes

- Services are functions, not classes.
- Stateless, no DI gymnastics.
- A service can call other services; a router can call any service.
- Testing: pass in a `db` session, call the function, assert on the result.

## What we DON'T do in the backend

- ❌ WebSockets. (ReelShort doesn't need them. Phase 5 if we add live comments.)
- ❌ GraphQL. REST is enough; FastAPI + Pydantic generates OpenAPI which the mobile client uses.
- ❌ gRPC. Mobile doesn't benefit.
- ❌ ORM triggers / events for audit. We write `audit_log` rows explicitly in services.
- ❌ Background tasks inside request handlers. Use `BackgroundTasks` for fast things, RQ for slow things.
- ❌ Storing JSON blobs in columns. If it's a list, it's a join table or a `text[]` column.
- ❌ Soft-delete everywhere. Only on `users` (for the 30-day restore window).
- ❌ Tailwind / template engines / Jinja. The backend returns JSON. Period.
