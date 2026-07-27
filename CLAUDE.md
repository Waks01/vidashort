# vidashort — project entry point

You are working on **vidashort**, a ReelShort / HiDrama-style microdrama app for the Nigerian market (and pan-African expansion). This file is the on-ramp. **Read it before you touch anything.**

## 1. What vidashort is

- Short-form vertical microdramas (1–3 min episodes, swipe-up feed, "unlock next episode" paywall).
- Hybrid catalog: in-house originals + creator-uploaded UGC.
- Monetization: coins (real money via IAP) + rewarded ads + VIP subscription.
- Creator economy: 60/40 split, OPay / PalmPay / Moniepoint / bank cashout.
- 17+ age-gated, ad-funded + paywall. Aggressive engagement loops. Dismissible paywalls (App Store rule).

## 2. Repository shape

```
vidashort/
├── apps/
│   ├── design/        ← clickable HTML/CSS/JS visual prototype (the source of truth for the look)
│   ├── api/           ← FastAPI backend (Phase 2+)
│   └── mobile/        ← Expo app (Phase 1+)  [moved from /mobile in Phase 1 setup]
├── mobile/            ← Expo SDK 57 skeleton (will move into apps/mobile/ in Phase 1)
├── packages/
│   └── shared/        ← shared TS types + zod schemas (Phase 1+)
├── docs/              ← YOU ARE HERE. All architecture, API, brand, phase specs.
├── .claude/           ← Claude Code local config (settings.local.json, plans/)
└── README.md          ← human-facing readme
```

**Status:** Phase 0.5 (visual prototype) complete. `apps/api/` skeleton is in place from Phase 2; mobile route shell lives in `mobile/` and is moving into `apps/mobile/` as part of Phase 1. The first round of real implementation is Phase 1 (Expo routes + design system) and Phase 2 (real backend endpoints).

## 3. The "source of truth" hierarchy (read in this order)

1. **`docs/brand/00-overview.md`** — brand identity, colors, typography, voice. Non-negotiable.
2. **`docs/architecture/00-overview.md`** — high-level system diagram, the three apps, how they talk.
3. **`docs/steering/00-rules.md`** — what to do and what NOT to do. Hard constraints.
4. **`docs/phases/00-roadmap.md`** — which phase we're in and what's next.
5. **The active phase spec** (e.g. `docs/phases/01-mobile-skeleton.md`) — concrete tasks for this round.
6. **The component tree for what you're building** (e.g. `docs/mobile/00-tree.md` if mobile, `docs/backend/00-tree.md` if API).
7. **The API contract** (`docs/api/00-overview.md`) — every endpoint you'll call or implement.
8. **The frontend↔backend contract** (`docs/contracts/00-overview.md`) — how auth, errors, caching, video URLs work end-to-end.

If a phase spec and a contract disagree, **the contract wins** (it's what production code will speak). If a contract and the design prototype disagree, **the prototype wins** for look-and-feel, but the **contract wins** for behavior.

## 4. Currently locked-in numbers (do not change without the user)

| Locked value | Number | Source |
|---|---|---|
| Coin ↔ Naira | 10 coins = ₦1 | Round 2 |
| Episode unlock cost | 25 coins (₦2.50) | Round 2 |
| Rewarded ad reward | 20 coins (₦2.00) | Round 2 |
| Daily ad cap (per user) | 100 | Round 2 |
| Creator / platform split | 60% / 40% | Round 2 |
| Min creator payout | ₦5,000 (50,000 coins) | Round 2 |
| Paywall decision order | VIP → coins → ad → premium | Round 2 |
| Age gate | 17+ | ReelShort parity |
| Default currency display | Naira (₦) | Market |
| Payout methods | OPay, PalmPay, Moniepoint, Bank | Round 2 |

**If a task requires changing any of these, stop and ask the user first.** These are the economics of the product.

## 5. Stack

| Layer | Choice | Notes |
|---|---|---|
| Visual prototype | Plain HTML + CSS + vanilla JS, no build | `apps/design/` is self-contained, opens in any browser |
| Mobile | Expo SDK 57, expo-router, React 19.2, RN 0.86, TypeScript 6 | Read `mobile/AGENTS.md` before writing RN code — Expo SDK 57 is new. |
| Backend | FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic | Python 3.12 |
| Database | Postgres (Neon) | Append-only ledger for `coin_txn` |
| Cache / rate limit | Redis (Upstash) | Daily ad cap counter |
| Video | Cloudflare Stream | Signed playback URLs, 1h TTL |
| Auth (subscription) | RevenueCat | Wraps Apple IAP + Google Play sub |
| Auth (identity) | Email/password + Apple + Google | Apple via Sign in with Apple, Google via Google Identity |
| Ads | AppLovin MAX (primary) + AdMob (fallback) | S2S rewarded callbacks to our backend |
| Hosting | Fly.io (api) + EAS (mobile builds) | Phase 5 |
| Analytics | Sentry (errors) + PostHog (product) | Phase 5 |

## 6. What you CAN do without asking

- Edit files inside `apps/design/` to fix the visual prototype.
- Add new screens or states to the visual prototype (mirror the existing `*.html` + chrome.js pattern).
- Run any tests, lints, or build commands the user explicitly named.
- Read any file.
- Use `WebSearch` and `WebFetch` for docs (Expo, FastAPI, Cloudflare, RevenueCat). Permissions allow `apkpure.com` and `play.google.com` only; for everything else, ask first.

## 7. What you MUST ask before doing

- **Creating new dependencies** in `package.json` or `pyproject.toml`.
- **Deleting or renaming files** (especially in `apps/design/screens/` or `docs/`).
- **Changing any locked number** (see §4).
- **Any action that spends money or hits a real API** (Cloudflare, RevenueCat, App Store, Google Play, TMDB).
- **Pushing to a remote**, opening a PR, or running a deploy.
- **Touching `localStorage` keys that already exist** in `vidashort.*` — schema change is breaking.

## 8. The 4 working directories (Windows / OneDrive reality)

- Primary working directory: `C:\Users\kenik\OneDrive\Pictures\vidashort`.
- The `apps/design/` prototype is < 1 MB, OneDrive-safe.
- The `mobile/` and future `apps/mobile/` directories will get `node_modules/` (~600 MB) — must be excluded from OneDrive sync. See `docs/runbooks/onedrive-exclude.md` (Phase 1 task).
- The future `apps/api/` will get `.venv/` and `__pycache__/` — same exclusion needed.

## 9. How to navigate the docs

| If you want to… | Read |
|---|---|
| Understand the brand / colors / type | `docs/brand/00-overview.md` |
| See the system diagram | `docs/architecture/00-overview.md` |
| Know what NOT to do | `docs/steering/00-rules.md` |
| Know what phase we're in | `docs/phases/00-roadmap.md` |
| Build a mobile screen | `docs/mobile/00-tree.md` + the matching `docs/phases/0X-*.md` |
| Build a backend endpoint | `docs/backend/00-tree.md` + `docs/api/00-overview.md` + the matching phase spec |
| Know what an endpoint does | `docs/api/` (one file per domain) |
| Know how the app talks to the API | `docs/contracts/00-overview.md` |
| Find a runbook | `docs/runbooks/` |

## 10. OneDrive + path notes

- All paths in this doc tree use forward slashes (POSIX style) for consistency; Windows is fine with them.
- When the user says "the docs" or "the brand doc", they mean files in `docs/`. When they say "the plan", they mean `C:\Users\kenik\.claude\plans\harmonic-watching-knuth.md`.
- The plan file is the **session log** of decisions. The `docs/` tree is the **durable spec** that survives across sessions.

---

## 11. Common commands

The repo has two workspaces today (`mobile/` + `packages/shared/`) and a Python app under `apps/api/`. The root `package.json` exposes convenience proxies; per-app commands live in each app's `package.json` / `pyproject.toml`.

### Mobile (Phase 1+)

```bash
npm install                         # one-time, ~5 min (node_modules ~600 MB — exclude from OneDrive)
npm run mobile                      # cd mobile && npx expo start
npm run typecheck                   # cd mobile && npx tsc --noEmit
npm run lint                        # cd mobile && npx expo lint
# platform-specific (run inside mobile/):
npx expo start --android            # Android emulator
npx expo start --ios                # iOS simulator
npx expo start --web                # web preview
npm run reset-project               # nukes app/, restores app-example/
```

Mobile uses **Node 22** (`.nvmrc`) and Expo SDK 57 — read `mobile/AGENTS.md` before writing any RN code; Expo SDK 57 is new and the API differs from SDK 53/54.

### Backend (Phase 2+, `apps/api/`)

```bash
cd apps/api
docker compose up -d                # postgres:16 + redis:7 (host ports 5432, 6379)
uv sync                             # install Python deps (Python 3.12, uv-managed)
uv run alembic upgrade head         # apply migrations
uv run uvicorn app.main:app --reload # http://localhost:8000, /docs for Swagger
uv run python scripts/seed.py       # seed test user + Breaking Bad series
uv run python scripts/verify_e2e.py # smoke every endpoint end-to-end
uv run pytest tests/                # run pytest (asyncio_mode=auto)
```

The API container in `docker-compose.yml` runs on port 8000 with Postgres + Redis on the default ports; `DATABASE_URL` and `REDIS_URL` are baked into the compose env block.

### Visual prototype (Phase 0.5, `apps/design/`)

No build. Open `apps/design/index.html` in any browser. Shared chrome lives in `apps/design/scripts/chrome.js`; mock data in `apps/design/scripts/data.js`; design tokens in `apps/design/styles/tokens.css`.

### Pointing the mobile app at a local backend

```bash
# apps/mobile/.env (gitignored)
echo EXPO_PUBLIC_ENV=dev > apps/mobile/.env
echo EXPO_PUBLIC_API_URL=http://localhost:8000/v1 >> apps/mobile/.env
# iOS simulator reaches localhost:8000 directly.
# Android emulator: use http://10.0.2.2:8000/v1 instead.
```

## 12. Architecture at a glance

### Mobile (`mobile/`, moving to `apps/mobile/`)

**expo-router route groups** under `mobile/src/app/`:
- `(auth)/` — splash → onboarding → genre → age-gate → role → auth-entry → sign-up/in/forgot/otp
- `(viewer)/` — home, discover, search, library, wallet, profile (role-aware bottom nav)
- `(creator)/` — dashboard, series, upload, analytics, payouts
- `(admin)/` — overview, moderation, content, users, ads, finance

**Source layering** under `mobile/src/`:
- `app/` — file-based routes (expo-router, typed routes enabled in `app.json`)
- `components/` — UI primitives (own design system; no Paper / NativeBase / styled-components)
- `lib/` — `api/` (mock client that mirrors real backend shapes), `theme/` (token module, mirrors `docs/brand/20-tokens.md`), `storage/` (secure-store wrapper)
- `hooks/` — shared React hooks (queries via `@tanstack/react-query`)
- `types/` — TS types (some shared with `packages/shared/`)

**Key dependencies:** expo-router 57, react 19.2, RN 0.86, TypeScript 6, `@tanstack/react-query`, `react-native-reanimated` 4.5, `expo-image`, `expo-secure-store`, `react-native-purchases` (RevenueCat), `react-native-applovin-max`, `react-native-admob`.

### Backend (`apps/api/`)

**FastAPI layered structure** (see `app/main.py` for the wiring):
- `app/main.py` — app factory, CORS, lifespan logging, all routers under `/v1/`
- `app/routers/` — one file per API domain: `auth`, `me`, `content`, `entitlement`, `coins`, `ads`, `creator`, `admin`, `webhooks`
- `app/services/` — business logic. Hot files: `paywall.py` (locked decision order), `ad_cap.py` (Redis daily cap), `revenue_split.py` (60/40 creator math), `auth.py`, `coins.py`, `content.py`, `creator.py`
- `app/schemas/` — Pydantic v2 request/response shapes (one file per domain)
- `app/db/models/` — SQLAlchemy 2 async models (14 tables, see `docs/backend/10-schema.md`)
- `app/db/session.py` — async engine + session factory
- `app/core/` — `config` (Pydantic Settings), `deps` (DI), `errors` (error envelope), `logging` (structlog), `security` (JWT + bcrypt)
- `app/integrations/` — thin wrappers: `cloudflare_stream`, `revenuecat`, `applovin`, `apple`, `google`, `tmdb`

**Locked paywall decision order** (in `app/services/paywall.py`): VIP → coins → ad → premium. The paywall service is the single source of truth — every router calls it, no shortcuts.

### Shared package (`packages/shared/`)

Zod schemas consumed by both mobile (Phase 1+) and backend tests (Phase 2+). Importable as `@vidashort/shared`. Keeps wire-level shapes in one place so contract drift is a type error, not a runtime 4xx.

### How the three apps talk

```
[Mobile (Expo)] ── HTTPS ─▶ [FastAPI on Fly.io / local]
                              │
                              ├── Postgres (Neon) — users, series, episodes, ledger
                              ├── Redis (Upstash) — ad cap, idempotency keys, sessions
                              ├── Cloudflare Stream — signed playback URLs (1h TTL)
                              ├── RevenueCat — IAP webhook → /v1/webhooks/revenuecat
                              ├── AppLovin MAX — S2S reward callback → /v1/webhooks/applovin
                              └── TMDB — seed script only (Phase 2.5)
```

Auth flow, error envelope, idempotency rules, video URL TTLs, IAP receipt handling — all in `docs/contracts/00-overview.md`. The contract is what production code speaks; the prototype's mock shapes must match it.

---
