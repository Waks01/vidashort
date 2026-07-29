# Runbook — Provisioning (Neon + Upstash + Fly.io)

Phase 2 spec §6 ("Provisioning") lists three cloud accounts the API needs to run in any environment that's not your laptop. This runbook walks through each in 5 minutes. Total cost in free tiers: $0. Each step has a copy-pasteable command.

## What's needed and why

| Service | Role | Free tier |
|---|---|---|
| **Neon** | Postgres for `users`, `user_identities`, `refresh_tokens`, `email_otp`, `password_reset`, `coin_txn`, etc. | 0.5 GB, 190 compute hours/mo |
| **Upstash** | Redis for sign-in rate-limit + ad-cap counter | 10k requests/day, 256 MB |
| **Fly.io** | Hosts the FastAPI app (Dockerfile + `uvicorn app.main:app`) | 3 shared VMs, 256 MB each |

All three are managed (no DBA / no infra to babysit). Fly.io runs the API; Neon + Upstash are serverless data planes we connect to from Fly.

## Pre-flight

1. Install the Fly.io CLI: <https://fly.io/docs/hands-on/install-flyctl/>
2. Sign up: <https://fly.io/app/sign-up> (GitHub OAuth — no credit card needed for free tier)
3. Install the Neon CLI: `npm i -g neonctl` (or just use the web console)
4. Install the Upstash CLI: `npm i -g @upstash/cli` (or just use the web console)

The web console is faster for one-off setup. Use the CLI when you script it.

---

## Step 1 — Neon (Postgres)

1. Go to <https://console.neon.tech> and create a project named `vidashort-staging`.
2. Pick the **closest region** to your Fly.io app (default: `iad` for US-East). ReelShort parity = Nigeria eventually, so `fra` (Frankfurt) is also a fine choice.
3. **Branch:** keep `main`. Default Postgres version is fine.
4. Copy the **pooled connection string** (the one with `-pooler` in the hostname) — that's the one to use in production. Looks like:
   ```
   postgresql+asyncpg://neondb_owner:•••••••••••@ep-foo-123456.us-east-2.aws.neon.tech/vidashort?sslmode=require
   ```
5. The connection string goes into your `.env` as `DATABASE_URL`. Don't commit `.env`.

**Verify locally** that you can connect:

```bash
cd apps/api
uv run python -c "
import asyncio, asyncpg
async def main():
    conn = await asyncpg.connect('YOUR_CONNECTION_STRING_HERE')
    rows = await conn.fetch('SELECT 1')
    print(rows)
asyncio.run(main())
"
# → [{'?column?': 1}]
```

---

## Step 2 — Upstash (Redis)

1. Go to <https://console.upstash.com> and create a database named `vidashort-staging`.
2. **Type:** Regional. **Region:** match Neon (same `iad` / `fra`).
3. **Eviction:** off (we want predictable counts).
4. Copy the **Redis URL** (looks like `rediss://default:••••••@apn1-…-1.upstash.io:6379`). The `rediss://` prefix is correct — Upstash requires TLS.
5. Put it in `.env` as `REDIS_URL`.

**Verify locally:**

```bash
cd apps/api
uv run python -c "
import asyncio, redis.asyncio as redis
async def main():
    r = redis.from_url('rediss://default:…@…upstash.io:6379')
    print(await r.ping())
asyncio.run(main())
"
# → True
```

---

## Step 3 — Fly.io (API host)

1. From the repo root, launch the app (creates the Fly app, no deploy yet):
   ```bash
   cd apps/api
   fly launch --no-deploy \
     --name vidashort-api-staging \
     --region iad \
     --internal-port 8000
   ```
   When it asks "Do you want to tweak settings?", say **No**. The `fly.toml` is generated; commit it.

2. Set the secrets. Use the Neon + Upstash strings from above:
   ```bash
   fly secrets set \
     DATABASE_URL="postgresql+asyncpg://neondb_owner:…@ep-foo.us-east-2.aws.neon.tech/vidashort?sslmode=require" \
     REDIS_URL="rediss://default:…@…upstash.io:6379" \
     JWT_SECRET="$(openssl rand -hex 32)" \
     JWT_ALGORITHM="HS256" \
     ACCESS_TTL_S="3600" \
     REFRESH_TTL_S="2592000" \
     CORS_ORIGINS="*" \
     RESEND_API_KEY="" \
     RESEND_EMAIL_FROM="noreply@vidashort.app" \
     ENV="staging"
   ```
   The empty `RESEND_API_KEY=""` makes the email service take its dev-log branch so the smoke test below prints the OTP to the server log instead of trying to email anyone.

3. First deploy:
   ```bash
   fly deploy
   ```
   Output ends with `… successfully deployed`. Note the URL — `https://vidashort-api-staging.fly.dev`.

---

## Step 4 — Run the migrations

The migrations are checked into `apps/api/migrations/`. Apply them to Neon:

```bash
cd apps/api
# Local alembic talks to Neon via the same DATABASE_URL — Fly never runs migrations.
DATABASE_URL="postgresql+asyncpg://neondb_owner:…@ep-foo.us-east-2.aws.neon.tech/vidashort?sslmode=require" \
  uv run alembic upgrade head
# → Running upgrade  → 0001_initial, 0002_email_otp, 0003_users_email_verified
```

Verify the tables exist:

```bash
DATABASE_URL="…" uv run python -c "
import asyncio, asyncpg
async def main():
    c = await asyncpg.connect('…')
    rows = await c.fetch(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\")
    for r in rows: print(r['tablename'])
asyncio.run(main())
"
# → users, user_identities, refresh_tokens, email_otp, alembic_version, …
```

---

## Step 5 — Smoke test the deploy

This is the exact block from the Phase 2 spec §Verification:

```bash
API=https://vidashort-api-staging.fly.dev

# 1. Health (DB + Redis both up)
curl -s $API/health | jq
# → {"ok": true, "db": "ok", "redis": "ok"}

# 2. Sign up — must be 202 with requiresVerification
curl -s -o /dev/null -w "%{http_code}\n" -X POST $API/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"smoke@example.com","password":"correct-horse-battery","name":"Smoke"}'
# → 202

# 3. Fly logs print the OTP (because RESEND_API_KEY is empty)
fly logs | grep "DEV OTP"
# → DEV OTP — Your vidashort verification code
# →   to: smoke@example.com
# →   Your vidashort verification code is: 482917
# →   …

CODE=482917   # paste the code you see

# 4. Verify OTP — 200 with AuthResponse
curl -s -X POST $API/v1/auth/otp/verify \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"smoke@example.com\",\"code\":\"$CODE\"}" | jq
# → {"user":{"id":"…","email":"smoke@example.com","name":"Smoke","role":"viewer",…},
#    "accessToken":"eyJ…","refreshToken":"uId…"}

# 5. /v1/me with that token
TOKEN=eyJ…
curl -s -H "Authorization: Bearer $TOKEN" $API/v1/me | jq
# → {"user":{"…","email":"smoke@example.com",…},
#    "wallet":{"coins":0,"vip":{"active":false,"until":null}},
#    "adCap":{"used":0,"limit":100,"remaining":100,"resetsAt":"…"},
#    "streak":{"day":0,"lastClaimedOn":null}}
```

If every step above returns the documented status + payload, the staging API is live and Phase 2 verification passes.

---

## Step 6 — Point the mobile app at staging

In `mobile/.env` (gitignored):

```dotenv
EXPO_PUBLIC_ENV=staging
EXPO_PUBLIC_API_URL=https://vidashort-api-staging.fly.dev
```

Re-launch Expo (`npx expo start --ios`). Sign up with a fresh email — it should hit the real backend, the OTP will be printed to `fly logs`, and `/v1/me` will populate the wallet / adCap / streak from real Neon data.

---

## Cost & limits to watch

- **Neon free tier:** 0.5 GB. `coin_txn` is append-only and grows; if you let staging run for a month with real ad impressions, you may need to scale up.
- **Upstash free tier:** 10k commands/day. The ad-cap counter + signin rate-limit both hit it; one sign-in attempt = 2 commands (INCR + maybe EXPIRE), so 10k attempts/day is the ceiling. Plenty for staging.
- **Fly.io free tier:** 3 shared VMs at 256 MB. The app boots in ~200 MB; budget the rest for requests. If you see OOM, `fly scale memory 512`.

---

## What to do when something is broken

- **`/health` returns 503 with `db: down`** — Neon is unreachable. Check the connection string. Test it with `psql` first.
- **`/health` returns 503 with `redis: down`** — Upstash is unreachable. Check the URL has `rediss://` (TLS) not `redis://`.
- **`alembic upgrade head` fails** — most likely Neon has a branch / role mismatch. Drop the database and recreate it; rerun.
- **Mobile app shows "Network request failed"** — CORS. `CORS_ORIGINS` is `"*"`, so it shouldn't be that. Check `EXPO_PUBLIC_API_URL` doesn't have a trailing slash; `https://foo.fly.dev` (no slash) is right, `https://foo.fly.dev/` (slash) breaks the path concat.
- **Mobile app gets `401` immediately after signup** — the OTP was never verified, so the access token is null. The mobile flow is sign-up → OTP screen → verify → home. If you skipped OTP, you got the `{ok, requiresVerification}` 202 and no tokens. Check `fly logs` for the OTP code.

See `debugging.md` for the full diagnostic flow.