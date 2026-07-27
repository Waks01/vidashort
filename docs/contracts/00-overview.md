# Frontend ↔ Backend contract

The wire-level contract between `apps/mobile/` and `apps/api/`. If you're writing either side, read this first. **This doc wins over the design prototype for behavior.**

## 1. Auth flow

### Sign-up / sign-in

```
Mobile: tap "Sign up" → fill form
Mobile: POST /v1/auth/signup { email, password, name, acceptedTerms }
Server: creates users + user_identities rows
Server: generates accessToken (JWT, 1h) + refreshToken (opaque, 30d)
Server: refresh token's SHA-256 stored in refresh_tokens table
Server: returns { user, accessToken, refreshToken }
Mobile: stores both tokens in expo-secure-store
Mobile: navigates to (viewer)/home
```

### Token storage

- **expo-secure-store only.** Not MMKV, not AsyncStorage, not Redux, not localStorage.
- Per-app, encrypted with the device's secure enclave.
- Tokens never leave secure-store except inside `Authorization: Bearer ...` headers.

### Access token (JWT)

- HS256 signed with `JWT_SECRET` (env var on server).
- Payload: `{ sub: <userId>, email, role, vip, iat, exp }`.
- TTL: 1 hour.
- The `vip` flag is a fast-path; the actual entitlement check always re-reads from `vip_entitlements`.

### Refresh token (opaque)

- 256-bit random, base64url-encoded.
- TTL: 30 days.
- Server stores only the SHA-256; raw is never persisted.
- On every refresh, **a new pair is issued and the old refresh is marked `used_at = now()`**. Rotation prevents replay.
- If a `used_at` refresh is presented (replay attempt), all of the user's refresh tokens are invalidated. Possible stolen token, force re-signin.

### Auto-refresh

```
Mobile: any request
  → 401 from server
Mobile: POST /v1/auth/refresh { refreshToken }
  → 200: { accessToken, refreshToken }
  → or 401: refresh is dead, sign out
Mobile: retry original request once with new accessToken
```

If the retry 401s too, or the refresh itself 401s, **wipe all tokens** and route to sign-in.

### Sign-out

```
Mobile: clear secure-store
Mobile: POST /v1/auth/signout (optional; JWTs are stateless)
Server: marks all of user's refresh_tokens.used_at = now()  (revoke them)
```

JWT access tokens remain valid until they expire (1h max). Refresh revocation is what actually kills the session. This is a known limitation of stateless JWTs; the trade-off is worth it for the perf gain.

## 2. Error handling

### Server returns

Every error response has the same envelope:

```json
{
  "error": "snake_case_code",
  "message": "Human readable",
  "details": { ... }  // optional
}
```

### Mobile handles

```ts
// lib/api/client.ts throws structured errors
class ApiError extends Error {
  constructor(
    public code: string,        // "entitlement_required"
    public status: number,      // 403
    public body: any,           // the full response body
  ) { super(body.message); }
}
```

### The 6 error patterns the mobile app knows

| Code | What mobile does |
|---|---|
| `entitlement_required` | Open the paywall modal, render the CTA from `details.paywall`. |
| `ad_cap_reached` | Toast "Daily ad cap reached. Come back tomorrow." |
| `vip_required` | Route to the VIP screen. |
| `user_banned` | Show "Your account is suspended" full-screen, link to support. |
| `user_deleted` | Show "Restore account?" with 30-day countdown. |
| `rate_limited` | Toast "Slow down a sec" and respect `Retry-After`. |
| `*` (anything else 4xx) | Toast `body.message`. |
| `5xx` | Toast "Something went wrong" + log to Sentry + retry once with backoff. |

### Network errors

- No response at all (timeout, no internet) → `NetworkError` → toast "No connection. Tap to retry."
- The user is not signed out on network errors (only on auth errors).
- 5xx → backoff retry 1s, 3s, 10s. After 10s, surface a toast.

## 3. Idempotency

For any non-idempotent operation, the mobile client generates a UUID and sends it as `Idempotency-Key` header:

```ts
// lib/api/coins.ts
purchase: (body: PurchaseRequest) => {
  const idempotencyKey = uuidv4();  // generated once, stored in MMKV with the receipt
  return apiFetch('/coins/purchase', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Idempotency-Key': idempotencyKey },
  });
}
```

The mobile persists the key in MMKV keyed by `packId + receipt.txnId`. On retry (network blip, app crash mid-flow), the same key is reused, the server returns the same response, the user sees the same outcome.

Endpoints that support idempotency:
- `POST /v1/coins/purchase` (required)
- `POST /v1/entitlement/unlock` (natural idempotency via `(user_id, episode_id)` unique constraint, but the key is still sent for safety)
- `POST /v1/ad/record` (unique constraint on `(user_id, ad_id)`)
- `POST /v1/creator/payouts` (creator can only have one pending; second call returns 409)

## 4. Caching strategy

The mobile app uses **react-query** for server data. Cache TTLs are per-endpoint, all from `constants/cache.ts`:

| Endpoint | staleTime | gcTime | Notes |
|---|---|---|---|
| `GET /v1/me` | 60s | 5 min | Re-fetch on app foreground |
| `GET /v1/content/featured` | 5 min | 30 min | The home feed |
| `GET /v1/content/series` | 5 min | 30 min | Discover |
| `GET /v1/content/series/{slug}` | 1 h | 24 h | Series detail (rarely changes) |
| `GET /v1/coins/packs` | 24 h | 7 d | Pack catalog (changes rarely) |
| `GET /v1/vip/plans` | 24 h | 7 d | |
| `GET /v1/ad/cap` | 0 (always fresh) | 1 min | Critical for paywall |
| `GET /v1/me` wallet, adCap | 0 | 0 | Always re-fetch on screen open |

### Invalidate on

- After any coin transaction → invalidate `me` and `coin_txn` cache.
- After VIP purchase → invalidate `me` (the `vip` flag is now correct).
- After favorite / unfavorite → invalidate `me` favorites and the series.
- After series detail load → invalidate the `featured` if the series was newly published.

### MMKV mirror

A few things are mirrored in MMKV for **offline / instant** use:
- User's coin balance (always re-validated against `/v1/me` on app open).
- Ad cap remaining (always re-validated against `/v1/ad/cap` on app open).
- Last 20 watch history entries (for "Continue Watching" offline).
- Favorites (for offline library).
- Search recent (purely local).

Everything else: react-query cache only, never MMKV.

## 5. The paywall flow (the most important)

This is the actual sequence. The mobile and server stay in sync via the same `decide()` algorithm.

### User taps an episode

```
Mobile: usePaywallDecision(episode)  // client-side fast path
       → returns { path: 'coins', cta: 'Use 25 coins', onPress: ... }
       → mobile may already show a paywall preview on the cost chip

Mobile: GET /v1/content/series/{slug}/episodes/{n}/stream
  → 200 { playbackUrl, ... }                          // free, play it
  → 403 { error: 'entitlement_required', details: { paywall: { path, costCoins, ... } } }
  → 4xx other → toast + don't auto-redirect
  → 5xx → retry with backoff
```

### If 403 (paywall)

```
Mobile: open paywall modal with the path from the server
        (server path wins, even if the client computed a different one)

User taps "Use 25 coins"
Mobile: POST /v1/entitlement/unlock { episodeId, source: 'coins' }
        Idempotency-Key: <uuid>
  → 200 { ok, source, coinsAfter, creatorCreditedCoins, playbackUrl }
Mobile: dismiss modal, navigate to player with playbackUrl from response
        (or re-call /stream if response didn't include it)
  → 403 { error: 'insufficient_coins' }  // user spent coins since the 403
  →    → re-render paywall with new state, ask user to try again
```

### If "Watch ad" path

```
Mobile: open paywall, user taps "Watch ad for +20 coins"
Mobile: AppLovin MAX SDK.showRewardedAd(...)
  → onRewardedAdCompleted → POST /v1/ad/record { adId, watchedS, completed: true }
  → 200 { ok, rewardedCoins, newBalance, remaining }
Mobile: now user has 20 coins (possibly +20 from the ad, more if they already had some)
Mobile: re-decide: probably "coins" now
Mobile: POST /v1/entitlement/unlock { episodeId, source: 'ad' }
        (the unlock uses the rewarded coins; the ad record and unlock record are separate)
```

## 6. Video playback

### Source URL

`GET /v1/content/.../stream` returns a `playbackUrl` that is a **signed Cloudflare Stream URL** with a 1-hour TTL. The mobile player:

- Fetches a fresh URL every time the user taps play (NOT while paused).
- Does NOT cache the URL in MMKV or anywhere else; it expires.
- Includes the `?expires=` query param from the response in the player's headers (Cloudflare rejects requests with expired sigs).

### Player lifecycle

```
User taps episode
  → GET /v1/content/.../stream  (fresh URL)
  → expo-video loads, starts playing
  → onProgressUpdate every 1s
  → PATCH /v1/watch_history { episodeId, positionS } every 10s
  → onComplete (currentTime >= duration - 2s)
       → GET /v1/content/featured?after={episodeId}  (next episode)
       → PATCH /v1/watch_history { episodeId, completed: true }
       → if episodesWatched % 3 == 0 → show interstitial
       → autoplay next episode OR open paywall
```

### Mid-roll ads

- The server returns `midrollAtS` in the stream response.
- The player listens for `onProgressUpdate` and at `midrollAtS`, pauses playback.
- A 5s in-player sponsored card overlay is shown.
- After 5s, playback resumes.
- For VIP users, `midrollAtS` is null → no midroll.

### Pre-roll ads

- The server returns `prerollAd: { adId, durationS }` in the stream response.
- The player shows this as a 3s mini-card before the episode starts.
- For VIP users, `prerollAd` is null → no preroll.

### Captions

- The server returns `captionsUrl` if the episode has captions.
- The player uses `expo-video`'s subtitle track API.
- Captions file is a WebVTT served from Cloudflare.

## 7. IAP (in-app purchase)

### On the client

```ts
// lib/iap/revenuecat.ts
import Purchases from 'react-native-purchases';

await Purchases.configure({ apiKey: RC_API_KEY });

// 1. Fetch offerings from RevenueCat
const offerings = await Purchases.getOfferings();
const monthly = offerings.current?.monthly;

// 2. User taps "Subscribe"
const { customerInfo } = await Purchases.purchasePackage(monthly);

// 3. Tell the server about the purchase (so it can mirror the state)
const res = await api.vip.subscribe({
  productId: monthly.identifier,
  receipt: customerInfo.originalAppUserInfo,  // RevenueCat's wrapper
  txnId: customerInfo.originalPurchaseDate,
});

// 4. Trust the webhook (don't trust the client response for state changes)
```

### On the server

The server's `/v1/vip/subscribe` endpoint:
1. Verifies the receipt with RevenueCat's REST API.
2. Creates / updates `vip_entitlements` row.
3. Returns the new VIP state.

The webhook from RevenueCat is the **authoritative** source. The client call is the UX accelerator.

### Refunds

- Apple / Google can refund a subscription. They notify us via webhook.
- We set `vip_entitlements.expires_at = refund_date` (effectively ending the VIP immediately).
- The user keeps VIP until the webhook fires (typically < 5 min).
- The webhook handler is in `services/revenuecat.py → handle_webhook()`.

## 8. Push notifications

- **Not in Phase 1.** Phase 4.
- The architecture: Expo Notifications, with a server-side queue (`push_notifications` table) that's drained by a worker (Phase 5).
- Permission is requested **after** a meaningful interaction, never on app launch. App Store rule.

## 9. Offline / no connection

- The app launches fine offline. It shows a cached version of the last `/v1/me` and the last 10 episodes.
- Any action that needs the server shows a toast "No connection" and is retried when online.
- The player refuses to play offline (we don't support offline downloads in Phase 1; Phase 5 if we have VIP).
- Favorites and watch history are queued for replay when the connection returns.

## 10. Environments

```ts
// constants/env.ts
const env = process.env.EXPO_PUBLIC_ENV as 'dev' | 'staging' | 'prod';

export const config = {
  apiUrl: {
    dev: 'http://localhost:8000/v1',
    staging: 'https://staging-api.vidashort.app/v1',
    prod: 'https://api.vidashort.app/v1',
  }[env],
  rcKey: {
    dev: 'appl_xxx_dev',
    staging: 'appl_xxx_staging',
    prod: 'appl_xxx_prod',
  }[env],
  sentryDsn: { dev: '', staging: '...', prod: '...' }[env],
};
```

`.env` (per developer, gitignored):
```
EXPO_PUBLIC_ENV=dev
EXPO_PUBLIC_API_URL=http://localhost:8000/v1
EXPO_PUBLIC_RC_KEY=appl_xxx_dev
```

## 11. Logging

- **In dev:** `console.log` is fine, with a small structured prefix.
- **In prod:** Sentry captures `console.error` and unhandled promise rejections automatically.
- **Never log:** tokens, refresh tokens, IAP receipts, password hashes, email content.
- Server-side: `structlog` with a request-id per request, propagated as `X-Request-ID` header to the client for support tickets.

## 12. The shape of a request

For reference, this is what every authenticated request looks like on the wire:

```http
GET /v1/me HTTP/1.1
Host: api.vidashort.app
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Accept: application/json
X-Request-ID: 01HXYZ...
User-Agent: vidashort/1.0.0 (iOS 17.5; iPhone15,3)
X-App-Version: 1.0.0
X-Platform: ios
```

And the response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: 01HXYZ...
X-RateLimit-Remaining: 599

{
  "user": { ... },
  "wallet": { "coins": 120, "vip": { "active": false, "until": null } },
  ...
}
```

The `X-Request-ID` is the single thread that ties a support ticket to a specific request. Always pass it through to Sentry.
