# Ads endpoints

Daily cap, rewarded-ad completion, ad inventory.

## Conventions

- Daily ad cap is **100 per user** (locked).
- Reset is at **UTC midnight** (not the user's local midnight — the cap is global).
- "Rewarded ad" = user opts in to watch an ad in exchange for coins.
- "Interstitial" = a full-screen ad between episodes (no reward). Tracked separately in `ad_impressions` for analytics, but no coin impact.
- Ad serving happens on-device via the AppLovin MAX SDK. The server only sees the S2S callback when a rewarded ad completes.

## Endpoints

### GET /v1/ad/cap

- **Auth:** required
- **Response 200:**
  ```json
  {
    "used": 4,
    "limit": 100,
    "remaining": 96,
    "resetsAt": "2026-07-23T00:00:00Z"
  }
  ```
- **Notes:**
  - `used` is the count of rewarded ads completed today (UTC).
  - `resetsAt` is the next UTC midnight as ISO 8601.
  - Wallet screen calls this to render "You've earned X coins today. Y more ads until cap."
  - The mobile client **mirrors** this value in MMKV for fast offline check, but the server re-checks on every `/ad/record`.

### POST /v1/ad/record

- **Auth:** required
- **Request:**
  ```json
  {
    "adId": "ad-unit-uuid",
    "watchedS": 15,
    "completed": true
  }
  ```
- **Response 200 (success):**
  ```json
  {
    "ok": true,
    "rewardedCoins": 20,
    "newBalance": 140,
    "remaining": 95
  }
  ```
- **Response 429 (cap reached):**
  ```json
  {
    "error": "cap_reached",
    "message": "You've reached today's ad cap. Come back tomorrow!",
    "details": { "resetsAt": "2026-07-23T00:00:00Z" }
  }
  ```
- **Errors:**
  - `400 watched_too_short` — watchedS < 5 (anti-cheat; the SDK enforces this too)
  - `400 already_recorded` — same `adId` already credited
  - `429 cap_reached`
  - `502 ad_network_unavailable` — AppLovin MAX is down
- **Side effects on success:**
  - `ad_impressions` row: `ad_id, watched_s, completed: true, rewarded_coins: 20`.
  - Redis: `INCR ad_cap:{user_id}:{date}` with `EXPIREAT` set to next UTC midnight.
  - Postgres: `users.coins += 20`, `coin_txn` row with `reason: "rewarded_ad"`.
  - The transaction is idempotent on `(user_id, ad_id)` — the same adId can never credit twice.

## How rewarded ads work end-to-end

```
1. User taps "Watch a quick ad for +20 coins" (on paywall, wallet, or daily reward).
2. Mobile: AppLovin MAX SDK.showRewardedAd('rewarded_20')
3. AppLovin: serves the ad, user watches.
4. AppLovin: on completion, fires 'onRewardedVideoCompleted' event in the SDK.
   Also makes an S2S callback to our server with the adId.
5. Mobile: on the SDK callback, fires POST /v1/ad/record.
6. Server: validates, checks cap, credits 20 coins, returns new balance.
7. Mobile: shows confetti + toast "+20 coins!"
```

The S2S callback (step 4b) is the **authoritative** record. The mobile call (step 5) is a UX accelerator so the user sees the +20 immediately. If the mobile call fails, the S2S callback still credits within 5s; the next `/v1/me` call reflects it.

## How the cap is enforced

Two layers:

1. **Client-side fast path** (`apps/mobile/src/lib/monetization/ad-cap.ts`):
   - Mirror the `remaining` from `/v1/ad/cap` in MMKV.
   - Hide the "Watch ad" button if `remaining === 0`.
   - This is UX, not security.

2. **Server-side authoritative** (`apps/api/app/services/ad_cap.py`):
   - Every `POST /v1/ad/record` checks Redis `ad_cap:{user_id}:{date}`.
   - If `INCR` returns > 100, the request is rejected.
   - The Redis key has a TTL of seconds until next UTC midnight.
   - Postgres `ad_impressions` is the durable record; Redis is the hot path.

## Anti-cheat

- `watchedS` must be ≥ 5 (server enforces).
- Same `adId` cannot credit twice (unique constraint on `(user_id, ad_id)`).
- Device fingerprint is sent in the mobile call (`deviceFingerprint` field, optional, Phase 4+).
- If we detect a pattern (e.g. one device with 10 accounts all hitting cap at the same time), we soft-ban the device for 24h.
- Refund: see `docs/contracts/00-overview.md § "Refunds"`.

## Interstitials (not rewarded)

Interstitials are **not credited** with coins. They exist to monetise free users between episodes.

- Every 3rd completed episode → interstitial.
- The mobile app fires `POST /v1/ad/impression` (separate from `/v1/ad/record`) for analytics.
- The user sees the ad (served on-device by AppLovin) and gets nothing. They just keep watching.

## What we track

For each `ad_impressions` row:
- `user_id` — who watched
- `ad_id` — the AppLovin ad unit ID
- `ad_network` — `appLovin`, `admob`, `unity`, etc. (we may add networks)
- `ad_type` — `rewarded` | `interstitial`
- `watched_s` — how long they actually watched
- `completed` — did they finish?
- `rewarded_coins` — 0 for interstitial, 20 for rewarded
- `country` — derived from request IP
- `app_version` — from the mobile client header
- `created_at`

This feeds admin dashboards and is the basis for the LTV calculation per ad network.
