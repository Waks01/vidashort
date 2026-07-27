# Architecture overview

## What we're building

A three-tier system:

```
┌─────────────────────┐         ┌──────────────────────┐         ┌──────────────────┐
│  apps/mobile (Expo) │ ──────► │   apps/api (FastAPI) │ ──────► │  Postgres (Neon) │
│                     │  HTTPS  │                      │         │  + Redis (Upstx) │
│  - React Native     │ ◄────── │  - auth              │ ◄────── │  + CF Stream     │
│  - expo-router      │  JSON   │  - content           │         │  + RevenueCat    │
│  - expo-video       │  JWT    │  - entitlement       │         │  + AppLovin MAX  │
└─────────────────────┘         │  - coins / ads       │         └──────────────────┘
                                │  - creator           │
                                │  - admin             │
                                └──────────────────────┘

            ▲
            │  (also reachable from)
            │
   ┌─────────────────────┐
   │  apps/design        │  ← static HTML prototype. No backend. Mock data only.
   │  (HTML/CSS/JS)      │     Reference implementation, not production.
   └─────────────────────┘
```

## The three apps

### `apps/design/` — visual prototype (Phase 0.5, complete)
- **Purpose:** Lock the look, the flows, the dark patterns. No framework, no build, no backend.
- **Size:** < 1 MB, 43 screens, 4 CSS files, 3 JS files.
- **Runtime:** Open any HTML file in a browser.
- **Persistence:** `localStorage` with the `vidashort.*` key namespace.
- **Deployment:** None. Just files.
- **Future:** Will be **read-only** after Phase 1 ships. It becomes the reference for designers and for screenshotting.

### `apps/api/` — FastAPI backend (Phase 2, design done)
- **Purpose:** Auth, content catalog, entitlement / paywall, coins, ads, creator + admin.
- **Stack:** FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic + python-jose + bcrypt + httpx.
- **Deployment:** Fly.io (or Render / Railway — TBD), autoscaling 1–4 instances.
- **Database:** Neon Postgres, 1 GB free tier initially, autoscale when paying.
- **Cache:** Upstash Redis, 10k commands/day free tier, daily ad cap counter.
- **External:** Cloudflare Stream (video), RevenueCat (subs), AppLovin MAX (ads), TMDB (posters).

### `apps/mobile/` — Expo app (Phase 1, design done)
- **Purpose:** The shipping product. iOS + Android from one codebase.
- **Stack:** Expo SDK 57, expo-router, React 19.2, RN 0.86, TypeScript 6.
- **Auth:** Apple Sign-In + Google Identity + email/password.
- **Video:** `expo-video` (replaces `expo-av`).
- **Payments:** RevenueCat (`react-native-purchases`).
- **Ads:** AppLovin MAX (`react-native-applovin-max`).
- **Push:** Expo Notifications.
- **Build:** EAS Build → TestFlight + Play internal track.

## How they talk

### Mobile → API

- **Protocol:** HTTPS + JSON. All routes prefixed `/v1/`.
- **Auth:** `Authorization: Bearer <jwt>` header on every authed request.
- **Tokens:** Access token (1h JWT) + refresh token (30d opaque). Stored in `expo-secure-store`.
- **Refresh:** Auto on 401, single retry per request. If refresh fails, wipe tokens, route to sign-in.
- **Errors:** Consistent envelope `{ error, message, details? }`. Status codes per contract in `docs/api/`.
- **Retries:** 5xx retries with backoff 1s/3s/10s. 4xx does not retry. 401 retries once after refresh.

### API → Postgres

- **Pool:** SQLAlchemy 2 async engine, 5–20 connections.
- **Migrations:** Alembic, run on every deploy.
- **Hot tables:** `series`, `episodes`, `coin_txn`, `watch_history`.
- **Indexes:** Per `docs/backend/00-tree.md § 3`.

### API → Redis

- **Used for:** daily ad cap counter (`ad_cap:{user_id}:{date}` → INCR + EXPIRE), session invalidation, rate limiting.
- **NOT used for:** source of truth. All writes go to Postgres first.

### API → Cloudflare Stream

- **Video upload:** API mints a signed upload URL, creator uploads directly to CF, CF webhook back to us.
- **Playback:** API mints a signed playback URL (1h TTL), returns in `GET /v1/content/.../stream`.
- **Signed URL key:** in `CF_STREAM_SIGNING_KEY` env var.

### API → RevenueCat

- **Inbound webhook:** `POST /v1/webhooks/revenuecat` on any subscription event → upsert `vip_entitlements`.
- **Outbound:** API doesn't call RevenueCat. The mobile SDK does. The webhook is the source of truth.

### API → AppLovin MAX

- **Mobile SDK** calls AppLovin for ad serving.
- **S2S callback:** AppLovin POSTs to our `POST /v1/ad/record` when a rewarded ad completes. We verify, credit 20 coins, return new balance.

## Data flow examples

### User opens the home feed
```
Mobile: GET /v1/content/featured
  → 200 { items: [{ episodeId, seriesId, slot }] }

Mobile: for each episode:
        GET /v1/content/series/{slug}
        GET /v1/content/series/{slug}/episodes/{n}/stream  # if user taps
```

### User taps a paywalled episode
```
Mobile: GET /v1/content/series/{slug}/episodes/{n}/stream
  → 403 { error: "entitlement_required", paywall: { path: "coins", cost: 25, ... } }

Mobile: shows paywall modal matching `path`
User: taps "Use 25 coins"
Mobile: POST /v1/entitlement/unlock { episodeId, source: "coins" }
  → 200 { ok, source, coinsAfter, creatorCreditedCoins: 15 }
Mobile: GET /v1/content/.../stream  (retry)
  → 200 { playbackUrl, ... }
```

### User completes a rewarded ad
```
Mobile: AppLovin SDK fires "ad_completed" event
Mobile: POST /v1/ad/record { adId, watchedS: 15, completed: true }
  → 200 { ok, rewardedCoins: 20, newBalance, remaining: 99 }
```

### Creator cashes out
```
Creator: POST /v1/creator/payouts { amountCoins: 50000 }
  → 201 { payout: { id, status: "pending", ... } }
Admin: POST /v1/admin/payouts/{id}/decide { decision: "approve" }
  → 200 { payout: { status: "approved" } }
  # Admin then transfers ₦5,000 manually via OPay dashboard, marks paid
```

## Repository layout

```
vidashort/
├── apps/
│   ├── design/        # visual prototype (Phase 0.5, complete)
│   ├── api/           # FastAPI backend (Phase 2)
│   └── mobile/        # Expo app (Phase 1)  [moved from /mobile in Phase 1 setup]
├── mobile/            # current Expo SDK 57 skeleton (will be moved)
├── packages/
│   └── shared/        # shared TS types + zod schemas (Phase 1+)
├── docs/              # the docs you are reading
├── .claude/           # Claude Code config
├── CLAUDE.md          # project entry point
├── README.md          # human readme
└── .gitignore
```

## Why three apps, not one

- **Prototype** must run with zero setup. Anyone can open an HTML file and see the design. No npm install, no Postgres, no FastAPI.
- **API** is its own thing because Python (data, ML, ops) is different from JS (product). Also, mobile needs a stable API contract to talk to.
- **Mobile** is the only thing the user touches. It deserves its own focused codebase.

## Why mobile is a monorepo package, not standalone

- Shared TypeScript types between mobile and (eventually) any scripts the user might run.
- One `git repo` to clone. One place to look for the truth.
- The `packages/shared/` directory will hold types that both mobile and the backend tests import (via Python's pydantic mirroring).

## Boundaries (what each app does and does NOT do)

| Concern | design | api | mobile |
|---|:---:|:---:|:---:|
| Render the UI | ✅ | ❌ | ✅ |
| Hold mock data | ✅ | ❌ | ❌ |
| Persist state | localStorage | Postgres + Redis | MMKV + secure-store |
| Authenticate | mock | ✅ | UI only (delegates to api) |
| Authorise | mock | ✅ | ❌ |
| Validate business rules | mock | ✅ | mirrors (fast-path UX) |
| Serve video | ❌ | mints URLs | plays URLs |
| Take payment | ❌ | verifies receipts | SDK + receipt upload |
| Show ads | ❌ | mock callbacks | SDK + S2S callbacks |
| Send notifications | ❌ | queues | local + push |
| Take screenshots for stores | ❌ | ❌ | ✅ (EAS) |
| Run automated tests | manual | pytest | jest + RNTL |

## Out-of-scope apps (do not create)

- ❌ An admin web app. Admin views are mobile screens. (`/v1/admin/*` exists; the UI lives in `(admin)/` route group in the mobile app, plus the role-switcher on `apps/design/index.html`.)
- ❌ A separate "creator studio web". Same — creator UI is mobile. (Some studios do want web; if the user asks for it in Phase 6, it's a new app, not a fork of mobile.)
- ❌ A "marketing site". Use a static page in `apps/design/` or a real CMS later. Not now.
- ❌ A "data pipeline" or analytics warehouse. PostHog is enough for now. Event log is in the API → Postgres for replay.

## What happens in each phase (one-line summary)

| Phase | What ships |
|---|---|
| 0.5 | Visual prototype (done) |
| 1 | Expo mobile skeleton: `(auth)/` route group, design system, 5-tab viewer shell, mock API client |
| 1.5 | OneDrive exclusions, EAS build, TestFlight + Play internal track |
| 2 | FastAPI backend skeleton: `/v1/auth/*`, `/v1/me`, `/health`, Neon + Upstash + Fly.io |
| 2.5 | Real auth (Apple + Google + email), Cloudflare Stream upload + signed playback, TMDB seed |
| 3 | Paywall, coins, ads, creator upload, RevenueCat, IAP verification |
| 4 | Comments, share, library, watch history, notifications, polish |
| 5 | Admin web/mobile, moderation, finance, payouts, observability |

See `docs/phases/00-roadmap.md` for the full breakdown.
