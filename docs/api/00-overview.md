# API surface — overview

## Base

- **Base URL (prod):** `https://api.vidashort.app/v1`
- **Base URL (staging):** `https://staging-api.vidashort.app/v1`
- **Base URL (dev):** `http://localhost:8000/v1` (via `EXPO_PUBLIC_API_URL`)
- **Protocol:** HTTPS in prod, HTTP only on localhost dev.
- **Content-Type:** `application/json` request and response.
- **Charset:** UTF-8.

## Auth

- **Header:** `Authorization: Bearer <accessToken>` on every authed route.
- **Access token:** JWT, 1h TTL, HS256 signed with `JWT_SECRET`.
- **Refresh token:** Opaque, 30d TTL, random 256-bit, sha256-hashed in DB, never raw.
- **On 401:** Client fires `POST /v1/auth/refresh`. If that 401s too, client wipes tokens, routes to sign-in.
- **No token in:** query string, request body (except `/v1/auth/refresh`), localStorage, AsyncStorage. Secure store only.

## Versioning

- All routes under `/v1/`.
- Breaking changes get `/v2/`. Non-breaking additions (new fields, new optional params, new endpoints) go into v1.
- v1 contract is frozen at first prod launch. After that, all changes are v2.

## Pagination

- Cursor-based, not offset-based. The cursor is opaque (base64 of `{ lastId, sortKey }`).
- Query: `?cursor=<opaque>&limit=20` (default 20, max 100).
- Response: `{ items: [...], nextCursor: "<opaque>" | null }`.
- Empty `items` + `nextCursor: null` = end of list.

## Filters and search

- Query params are AND'd: `?category=romance&source=tmdb&q=ceo`.
- Unknown query params are ignored (don't 400).
- `q` does a case-insensitive prefix match on `title` and a full-text match on `synopsis`. Postgres `pg_trgm` index.
- Sort: implicit by `total_episodes DESC, created_at DESC` for series, `created_at DESC` for lists.

## Money

- All money fields in API are **integers in coins.** Naira is display only.
- `1 coin = ₦0.10`, so `100 coins = ₦10`, `250 coins = ₦25`.
- Conversion in the client: `naira = coins / 10`. In the server, never. The server only ever deals in coins.
- Naira amounts in the API are floats, only used for displaying payouts. Storage is always coins.

## Error envelope (consistent across all routes)

```json
{
  "error": "snake_case_code",
  "message": "Human readable",
  "details": { "field": "error description" }
}
```

- `error` — machine-readable, snake_case, stable across versions.
- `message` — human-readable, may change between versions.
- `details` — only on validation errors. Keys are field names, values are errors.
- `details` is also used for paywall decisions (see `PaywallDecision` in `01-entitlement.md`).

## Status codes used

| Code | Use |
|---|---|
| 200 | OK, with body |
| 201 | Created (POST that creates) |
| 202 | Accepted, async (e.g. forgot-password always returns 202) |
| 204 | OK, no body (DELETE, PATCH that clears a field) |
| 400 | Bad request (malformed body, unknown enum, etc.) |
| 401 | Not authenticated (no token, expired token, bad refresh) |
| 403 | Authenticated but not allowed (paywall, wrong role, banned) |
| 404 | Resource doesn't exist |
| 409 | Conflict (e.g. email already registered) |
| 422 | Validation failed (form errors) |
| 429 | Rate limited or daily cap reached |
| 500 | Server error (should not happen; Sentry alerted) |
| 502 | Upstream error (TMDB, RevenueCat, Cloudflare) |
| 503 | Service unavailable (deploy in progress, db down) |

## Rate limits

- Anonymous: 60 requests / minute / IP.
- Authed: 600 requests / minute / user.
- IAP verification: 10 / minute / user (separate bucket, prevents receipt spam).
- Payout requests: 5 / day / creator.

Exceeding returns `429` with `{ error: "rate_limited", message: "Try again in N seconds" }`. The `Retry-After` header is set.

## Idempotency

- `POST /v1/coins/purchase` accepts an `Idempotency-Key` header. Same key returns the same response.
- All other POSTs are naturally idempotent or use the unique-constraint on the resource to prevent dupes.
- The mobile client generates a UUID per IAP receipt and sends it as the idempotency key.

## Timestamps

- All timestamps are ISO 8601 with timezone: `2026-07-22T11:00:00Z` (UTC).
- Client renders with `Intl.DateTimeFormat` using the device locale.

## CORS

- Allow: `https://vidashort.app`, `https://www.vidashort.app`, `https://admin.vidashort.app`, `exp://*` (Expo dev), `http://localhost:*` (dev).
- Methods: GET, POST, PATCH, DELETE, OPTIONS.
- Headers: `Content-Type`, `Authorization`, `Idempotency-Key`.
- Credentials: not used (we use bearer tokens, not cookies).

## Route map (one-line per route)

### Auth (`docs/api/01-auth.md`)
- `POST /v1/auth/signup` — create account with email + password
- `POST /v1/auth/signin` — sign in
- `POST /v1/auth/refresh` — rotate access token
- `POST /v1/auth/apple` — sign in with Apple
- `POST /v1/auth/google` — sign in with Google
- `POST /v1/auth/forgot` — request password reset
- `POST /v1/auth/reset` — complete password reset

### Me (`docs/api/02-me.md`)
- `GET /v1/me` — current user + wallet + ad cap + streak
- `PATCH /v1/me` — update profile
- `POST /v1/me/age-confirm` — record 17+ gate
- `DELETE /v1/me` — soft-delete + anonymise

### Content (`docs/api/03-content.md`)
- `GET /v1/content/series` — list series (paginated, filterable)
- `GET /v1/content/series/{slug}` — series detail with episodes
- `GET /v1/content/series/{slug}/episodes/{n}/stream` — playback URL (entitlement-gated)
- `POST /v1/content/{seriesId}/favorite` — add favorite
- `POST /v1/content/{seriesId}/unfavorite` — remove favorite
- `GET /v1/content/featured` — home feed config

### Entitlement (`docs/api/04-entitlement.md`)
- `POST /v1/entitlement/check` — would this episode be free for me?
- `POST /v1/entitlement/unlock` — pay (coins / ad / vip) to unlock

### Coins (`docs/api/05-coins.md`)
- `GET /v1/coins/balance` — current balance + recent transactions
- `GET /v1/coins/packs` — available packs
- `POST /v1/coins/purchase` — verify IAP receipt, credit coins

### Ads (`docs/api/06-ads.md`)
- `GET /v1/ad/cap` — current daily ad cap state
- `POST /v1/ad/record` — record a rewarded-ad view, credit coins

### Creator (`docs/api/07-creator.md`)
- `GET /v1/creator/profile` — creator's public profile
- `PATCH /v1/creator/profile` — update
- `GET /v1/creator/series` — own series
- `POST /v1/creator/series` — create draft series (returns upload URLs)
- `PATCH /v1/creator/series/{id}` — edit
- `POST /v1/creator/series/{id}/submit-for-review` — submit for moderation
- `GET /v1/creator/series/{id}/episodes/{n}/upload` — get signed upload URL
- `GET /v1/creator/analytics` — KPIs and time series
- `GET /v1/creator/earnings` — lifetime + pending earnings
- `POST /v1/creator/payouts` — request cashout
- `GET /v1/creator/payouts` — own payout history

### Admin (`docs/api/08-admin.md`)
- `GET /v1/admin/overview` — platform KPIs
- `GET /v1/admin/moderation` — moderation queue
- `POST /v1/admin/moderation/{id}/decide` — approve / reject
- `GET /v1/admin/content` — search all content
- `PATCH /v1/admin/content/{id}` — edit / hide / delete
- `POST /v1/admin/content/{id}/feature` — feature on home
- `GET /v1/admin/users` — search users
- `GET /v1/admin/users/{id}` — user detail
- `PATCH /v1/admin/users/{id}` — role, ban, refund
- `GET /v1/admin/ads` — ad campaigns
- `PATCH /v1/admin/ads/{id}` — pause / resume / change cap
- `GET /v1/admin/finance` — net revenue + ledger
- `POST /v1/admin/payouts/{id}/decide` — approve / reject creator payout

### Webhooks (`docs/api/09-webhooks.md`)
- `POST /v1/webhooks/cloudflare` — video processing complete
- `POST /v1/webhooks/revenuecat` — subscription event
- `POST /v1/webhooks/apple` — App Store Server Notification v2
- `POST /v1/webhooks/google` — Real-Time Developer Notification

## How to read the per-route docs

Each `docs/api/0X-*.md` file has the same structure:

```
# Domain name

## Conventions
- any domain-specific notes (e.g. "all times in UTC")

## Endpoints

### METHOD /v1/...
- **Auth:** required | admin | creator | public
- **Request:** JSON shape
- **Response 2xx:** JSON shape
- **Response 4xx/5xx:** error codes that may appear
- **Side effects:** what else happens (webhook, cache, etc.)
- **Notes:** gotchas, edge cases
```

Example: `docs/api/01-auth.md`.
