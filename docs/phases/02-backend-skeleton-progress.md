# Plan: Close Phase 2 (FastAPI backend skeleton) — 100% complete, nothing deferred

## Context

Per `docs/phases/00-roadmap.md` we're targeting Phase 2 → Phase 2.5 → Phase 3. Phase 2's spec (`docs/phases/02-backend-skeleton.md`) ends with **Mobile flip + CORS smoke test**: the mobile app at `EXPO_PUBLIC_ENV=staging` + `EXPO_PUBLIC_API_URL=…` should be able to sign up against a real running backend. Today the verification command in the spec literally cannot succeed:

1. **`mobile/src/lib/api/auth.ts` and `me.ts` are hard-coded re-exports of `./real/*`** — they bypass the env-aware selector at `lib/api/index.ts` entirely. No screen that imports `from '@/lib/api/auth'` ever sees the mock, regardless of `EXPO_PUBLIC_ENV`.
2. **`mobile/src/lib/api/real/client.ts:1`** uses `__DEV__ ? 'http://localhost:8000' : 'https://api.vidashort.app'`. `EXPO_PUBLIC_API_URL` (the env var the spec's verification command sets) is **never read**.
3. **`mobile/src/lib/api/real/me.ts`** defines `Me` as a flat `{id, email, coins, isVip, …}`. Backend `/v1/me` actually returns `{user: {…}, wallet: {coins, vip}, adCap: {used, limit, remaining, resetsAt}, streak: {day, lastClaimedOn}}` (camelCase via `BaseSchema` aliasing — verified in `tests/test_auth.py:294-314`). If we point mobile at the real backend today, every screen reading `user.coins` gets `undefined`.
4. **`tests/test_me.py` doesn't exist.** The `/v1/me` endpoint is tested inside `test_auth.py` (one happy-path + one 401), but the spec requires `me, update, age-confirm, delete`.
5. **`tests/test_health.py` doesn't exist.** Spec requires `/health` returns 200 with DB + Redis ping. Today `/health` just returns `{"ok": True}`.
6. **Rate limit not wired.** Spec requires "5 signin attempts / 10 min / user". `RateLimited` AppError exists in `app/core/errors.py` but no endpoint uses it.
7. **No Redis fixture.** Spec calls for `tests/conftest.py` to include a Redis fixture; `conftest.py` only sets `os.environ.setdefault("REDIS_URL", ...)`.
8. **No provisioning runbook.** Spec §6 lists Fly.io + Neon + Upstash provisioning; per user decision (this turn), this becomes `docs/runbooks/provisioning.md` rather than live setup.

Phase 2 cannot close without these. Goal of this plan: every deliverable in §1–§11 of the spec is either implemented or runbook'd. No deferring.

## Approach

The work splits into four independent threads that can mostly run in parallel. The mobile-flip thread depends on the backend thread completing first (so the contract it consumes is final).

### Thread A — Backend (closes spec §3, §5, §7, §8)

**1. `tests/test_me.py` (new).** Tests for `/v1/me`:
- `test_get_me_requires_auth` — no token → 401
- `test_get_me_returns_user_wallet_adcap_streak_payload` — full shape, `user.email`, `wallet.coins == 0`, `adCap.limit == 100`, `streak.day is None`
- `test_patch_me_updates_name_and_genres` — PATCH `/v1/me` with `{name, genres}` returns the new values
- `test_age_confirm_sets_age_confirmed_true` — POST `/v1/me/age-confirm` with `{confirmed: true}` → 204; subsequent GET reflects `ageConfirmed: true`
- `test_age_confirm_with_false_leaves_flag_unset`
- `test_delete_me_returns_204_and_user_gone` — DELETE → 204; subsequent GET → 401
- Reuse `_signup_and_verify` from `test_auth.py` for token minting, or import `signup_and_verify` from conftest.

**2. `tests/test_health.py` (new).** Tests for `/health`:
- `test_health_returns_ok` — 200 with `{"ok": True}`
- `test_health_returns_503_when_redis_down` — monkeypatch `get_redis().ping()` to raise → response is 503 (or matches whatever the new handler returns)
- Requires updating `app/main.py:62-64` `health()` to actually ping DB + Redis. If either fails, return 503 with `{"ok": false, "db": "ok"|"down", "redis": "ok"|"down"}`. The existing 200 path stays.

**3. Redis fixture in `tests/conftest.py` (modify).** Add a `redis_client` autouse fixture using `fakeredis.aioredis` (already in pyproject dev-deps via existing test infra — verify and add if missing per `pyproject.toml`). Wraps `app.db.session.get_redis` so the production code path is exercised without a live Redis server. **Decision gate**: if `fakeredis` isn't already a dep, ask user before adding (CLAUDE.md §7 forbids new deps without approval). If we can't add it, fall back to mocking `get_redis` directly via monkeypatch.

**4. Rate limit on `/v1/auth/signin` (modify `app/services/auth.py`).** Add a `check_signin_rate_limit(email, redis_client)` helper using Redis `INCR signin:attempts:{email}` + `EXPIRE 600`. Read inside `signin()` before bcrypt verify. Return `RateLimited` after the 5th hit. **Tests** in `tests/test_rate_limit.py` (new):
- `test_signin_rate_limit_blocks_after_5_attempts` — 5 wrong passwords → 6th returns 429
- `test_signin_rate_limit_resets_after_window` — TTL on the key is 600s; fast-forward by calling `redis.delete()` then verifying the user can sign in again
- `test_signin_rate_limit_is_per_email` — 5 attempts on alice@ don't block bob@

**5. `docs/runbooks/provisioning.md` (new).** Plain English + click-through. Sections: Fly.io (`fly launch --no-deploy`), Neon (project + connection string), Upstash (Redis + URL), `fly secrets set DATABASE_URL=... REDIS_URL=... JWT_SECRET=... RESEND_API_KEY=...`. Includes a "verify it works" curl block (signup → 202 → OTP verify → 200). Match the tone of `docs/runbooks/onedrive-exclude.md` (per CLAUDE.md §9 reference).

### Thread B — Mobile contract alignment (closes spec §10, prerequisite for mobile flip)

**6. Fix `mobile/src/lib/api/real/me.ts` `Me` interface (modify).** Replace the flat shape with the backend's actual one:
```ts
export interface Me {
  user: { id: string; email: string; name: string; role: 'viewer' | 'creator' | 'admin';
          avatarUrl: string | null; genres: string[]; language: string;
          ageConfirmed: boolean; onboarded: boolean; createdAt: string };
  wallet: { coins: number; vip: { active: boolean; expiresAt: string | null } };
  adCap: { used: number; limit: number; remaining: number; resetsAt: string };
  streak: { day: number | null; lastClaimedOn: string | null };
}
```

**7. Fix `mobile/src/lib/auth/provider.tsx` (modify).** Update the two places that read `user.coins` / `user.isVip` etc. — currently `setUser(data.user as unknown as Me)` (line 69, 83, 103) drops the wallet/adCap/streak parts. After this change, `setUser(data)` (full Me response). Confirm `getMe()` already returns full Me (it does, line 14-16 of `me.ts`). Net effect: `useAuth().user.wallet.coins` everywhere instead of `user.coins`.

**8. Fix `mobile/src/lib/api/real/client.ts:1` (modify).** Replace hardcoded URL with `process.env.EXPO_PUBLIC_API_URL ?? (__DEV__ ? 'http://localhost:8000' : 'https://api.vidashort.app')`. Single line change, matches the spec's verification env var. Also extract it as `export const BASE_URL` so the env-aware index can re-import it cleanly.

### Thread C — Mobile env-aware flip wiring (closes spec §10)

**9. Rewrite `mobile/src/lib/api/auth.ts` and `me.ts` (modify).** Both currently `export * from './real/auth'`. Change to:
```ts
import * as real from './real/auth';
import * as mock from './mock/auth';
const useReal = process.env.EXPO_PUBLIC_ENV === 'prod';
export const signup = useReal ? real.signup : mock.signup;
// … etc, mirroring lib/api/index.ts
```
This is the same pattern `lib/api/index.ts` already uses; we just replicate it for `auth.ts` and `me.ts` so the screens that import `from '@/lib/api/auth'` (forgot-password.tsx, reset-password.tsx, provider.tsx) and `from '@/lib/api/me'` (provider.tsx) flow through the selector.

**10. `mobile/src/app/(auth)/otp.tsx:27` `isMock` flag (modify).** Already reads `EXPO_PUBLIC_ENV !== 'prod'`. Confirmed correct — no change needed, just keep the consistency.

### Thread D — Verification (closes spec §11)

**11. New `tests/integration/test_signup_e2e.py`** (or just a manual curl block in `docs/runbooks/provisioning.md`). Smoke test the exact flow from spec:
```
POST /v1/auth/signup → 202 {ok, requiresVerification}
POST /v1/auth/otp/verify → 200 {accessToken, refreshToken, user}
GET  /v1/me (with token) → 200 {user, wallet, adCap, streak}
PATCH /v1/me → 200
POST /v1/me/age-confirm → 204
DELETE /v1/me → 204
```
Add as `tests/test_e2e_smoke.py` — reuses `client` fixture and `_signup_and_verify`. This is the "CORS + smoke test" deliverable.

## Critical files to modify

- `apps/api/tests/conftest.py` — add `redis_client` fixture (or monkeypatch get_redis)
- `apps/api/app/services/auth.py` — wire rate-limit INCR inside `signin()`
- `apps/api/app/main.py:62-64` — make `/health` actually ping DB + Redis, return 503 on failure
- `apps/api/tests/test_me.py` (new) — 6 tests for /v1/me
- `apps/api/tests/test_health.py` (new) — 2 tests for /health
- `apps/api/tests/test_rate_limit.py` (new) — 3 tests for the 5/10min limit
- `apps/api/tests/test_e2e_smoke.py` (new) — the spec's exact end-to-end curl sequence
- `docs/runbooks/provisioning.md` (new) — Fly.io + Neon + Upstash click-through
- `mobile/src/lib/api/real/me.ts` — fix `Me` interface to match backend shape
- `mobile/src/lib/api/real/client.ts` — read `EXPO_PUBLIC_API_URL`
- `mobile/src/lib/api/auth.ts` — route through env-aware selector (mirror `index.ts`)
- `mobile/src/lib/api/me.ts` — route through env-aware selector
- `mobile/src/lib/auth/provider.tsx` — preserve full Me (wallet/adCap/streak), not just inner user

## Critical files NOT to touch (out of Phase 2 scope)

- `apps/api/app/routers/{content,coins,ads,entitlement,creator,admin,webhooks}.py` — Phase 2.5/3
- `mobile/src/app/(viewer)/*.tsx` — Phase 2.5 (content wiring). The five-tab screens stay on mock for now; their `MockData` reads keep working because the env-aware flip still defaults to mock unless `EXPO_PUBLIC_ENV=prod`.
- `mobile/src/lib/api/real/content.ts` — Phase 2.5
- `mobile/src/lib/api/index.ts` — already correct, no changes needed
- `@vidashort/shared` schemas — Phase 2.5 (real contract sync)

## Existing utilities to reuse

- `tests/conftest.py:_EmailCapture` + `email_capture` autouse fixture — already capture-resend, no new mocking needed
- `tests/conftest.py:signup_and_verify` helper — full signup+verify+token-return flow
- `app/core/pydantic_base.BaseSchema` — `to_camel` aliasing means backend always returns camelCase; mobile types should match
- `app/db/session.get_redis` — already exported; we just need a test fixture for it
- `RateLimited` in `app/core/errors.py` — already defined; just need to raise it
- The handler at `app/main.py:30-38` for `AppError` — already maps to `{error, message}` envelope; RateLimited inherits from AppError so it works for free

## Verification

### Backend (after Thread A)

```bash
cd apps/api
uv run pytest tests/ -v
# Expect 67 + 6 (test_me) + 2 (test_health) + 3 (test_rate_limit) + 1 (test_e2e_smoke) = 79 passing
# Confirm no Phase 2 tests broke
```

### Manual curl smoke (Phase 2 spec verification, end-to-end)

```bash
# Pre-reqs: docker compose up -d, uv run alembic upgrade head, RESEND_API_KEY="" in .env
uv run uvicorn app.main:app --reload &

# Health
curl -s localhost:8000/health | jq  # → {ok: true, db: ok, redis: ok}

# Rate limit (5 wrong passwords)
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/v1/auth/signin \
    -H 'Content-Type: application/json' \
    -d '{"email":"rl@example.com","password":"wrong"}'
done  # → 400 400 400 400 429

# Full signup → OTP → me
curl -X POST localhost:8000/v1/auth/signup -H 'Content-Type: application/json' \
  -d '{"email":"e2e@example.com","password":"correctpw123","name":"E2E"}'
# → 202 {ok, requiresVerification}; OTP logged to stdout (dev mode)
CODE=$(grep "DEV OTP" server.log | tail -1 | grep -oE '[0-9]{6}')
curl -X POST localhost:8000/v1/auth/otp/verify -H 'Content-Type: application/json' \
  -d "{\"email\":\"e2e@example.com\",\"code\":\"$CODE\"}"
# → 200 with accessToken, refreshToken, user
TOKEN=...
curl -H "Authorization: Bearer $TOKEN" localhost:8000/v1/me | jq
# → 200 with {user, wallet, adCap, streak} — matches mobile Me interface
```

### Mobile (after Thread C)

```bash
# In apps/mobile/.env (gitignored)
EXPO_PUBLIC_ENV=staging
EXPO_PUBLIC_API_URL=http://localhost:8000
cd mobile && npx expo start --ios
# Sign up flow:
#   sign-up screen → POST /v1/auth/signup (real, not mock)
#   otp screen → copy code from server log → POST /v1/auth/otp/verify
#   home → user.wallet.coins = 0, user.adCap.remaining = 100, user.streak.day = null
# Switch EXPO_PUBLIC_ENV back to anything-but-prod to verify mock still works (screens render against MockData).
```

### TypeScript clean

```bash
cd mobile && npx tsc --noEmit
# 0 errors (the 4 pre-existing errors in scripts/start-expo-auto.ts are unrelated dev-script noise)
```

### Phase 2 spec checklist (each row closes):

| Spec row | Closed by |
|---|---|
| §1 Backend tree, pyproject, docker-compose, .env.example, main.py | Already done |
| §2 config, security, deps | Already done |
| §3 DB + 3 models + 0001 migration | Already done (extends to OTP table later) |
| §4 Auth router | Already done |
| §5 Errors + handlers | Already done |
| §6 Me router | Already done (extends to age-confirm, delete — already there) |
| §7 conftest + test_auth + test_me + test_health | **New: test_me.py, test_health.py, redis fixture in conftest** |
| §8 Rate limit | **New: wire signin → INCR + EXPIRE in auth.py, test_rate_limit.py** |
| §9 Provisioning | **New: docs/runbooks/provisioning.md** |
| §10 Mobile flip | **Modified: auth.ts/me.ts env-aware, client.ts reads EXPO_PUBLIC_API_URL, Me interface fixed, provider.tsx preserves full Me** |
| §11 CORS + smoke | CORS already in main.py:21-27; **New: test_e2e_smoke.py** |

## Order of execution

1. Thread A first (backend: test_me, test_health, redis fixture, rate limit). Run `pytest` after each file.
2. Thread B (mobile Me interface + provider fix + client.ts env var). Run `npx tsc --noEmit` after.
3. Thread C (mobile auth.ts/me.ts selector wiring). Run `npx tsc --noEmit` + manual Expo boot.
4. Thread D (test_e2e_smoke). Final `pytest` run.

Each thread is independent enough that errors in one don't block the others' types/tests passing.