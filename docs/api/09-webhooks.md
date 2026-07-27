# Webhook endpoints

External systems call us. All webhooks are public (no auth header) but **signature-verified**.

## Conventions

- All webhook bodies are JSON.
- Signature in header: `X-Vidashort-Signature: <hex sha256 hmac of body using shared secret>`.
- All webhooks are idempotent on the provider's event ID.
- All webhooks are fast: 200 returned within 200ms. Long work goes to a background task (FastAPI BackgroundTasks or RQ).

## Endpoints

### POST /v1/webhooks/cloudflare

- **Auth:** signature
- **Source:** Cloudflare Stream
- **Body (typical):**
  ```json
  {
    "uid": "abc123def456",
    "readyToStream": true,
    "status": { "state": "ready" },
    "duration": "1m32s"
  }
  ```
- **Response 202:** `{ "ok": true }`
- **Side effects:**
  - `episodes.video_ready = true` for the episode matching `uid`.
  - If all episodes of a series are ready and the series is `pending` review, mark it eligible for moderation.
  - Notify the creator: "Your video is ready for review."

### POST /v1/webhooks/revenuecat

- **Auth:** signature
- **Source:** RevenueCat
- **Body (typical):**
  ```json
  {
    "event": {
      "type": "INITIAL_PURCHASE" | "RENEWAL" | "CANCELLATION" | "EXPIRATION" | "BILLING_ISSUE" | "PRODUCT_CHANGE",
      "app_user_id": "vidashort-user-uuid",
      "product_id": "vip_monthly",
      "entitlement_ids": ["vip"],
      "expires_at": 1755854400000,
      "original_transaction_id": "...",
      "event_id": "..."
    }
  }
  ```
- **Response 202:** `{ "ok": true }`
- **Side effects:**
  - `INITIAL_PURCHASE` / `RENEWAL`: create or update `vip_entitlements` row with `expires_at`.
  - `CANCELLATION`: mark `vip_entitlements.auto_renew = false` (still active until expires_at).
  - `EXPIRATION`: delete or mark expired the `vip_entitlements` row.
  - `BILLING_ISSUE`: notify the user, mark row for retry.
  - Idempotent on `event.event_id`.
  - The mobile SDK also receives the same event; either side can write the row first, the other becomes a no-op.

### POST /v1/webhooks/apple

- **Auth:** signature (App Store Server Notification v2)
- **Source:** Apple App Store
- **Body (typical):** the signed payload from Apple, includes `signedPayload` (a JWS).
- **Response 202:** `{ "ok": true }`
- **Side effects:**
  - Decodes the `signedPayload` (JWS).
  - Extracts `notificationType` and `data` (a further-signed inner JWS).
  - Handles: `DID_RENEW`, `DID_FAIL_TO_RENEW`, `DID_CANCEL`, `EXPIRED`, `REFUND`.
  - Updates `vip_entitlements` or processes refund (`coin_txn` row, `delta: -<original purchase>`).
  - Idempotent on the `notificationUUID`.

### POST /v1/webhooks/google

- **Auth:** signature (Pub/Sub message in `message.data`, base64-encoded JSON)
- **Source:** Google Play
- **Body (typical):**
  ```json
  {
    "message": {
      "data": "<base64 of { subscriptionNotification: {...}, notificationType: 4, purchaseToken: '...' }>",
      "messageId": "..."
    }
  }
  ```
- **Response 202:** `{ "ok": true }`
- **Side effects:**
  - Decodes the inner payload.
  - Verifies the subscription via Play Developer API.
  - Updates `vip_entitlements` or processes refund.
  - Idempotent on `messageId`.

## Signature verification

```python
import hmac, hashlib

def verify_signature(secret: str, body: bytes, header: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)
```

Each provider has its own secret in env vars:
- `CF_WEBHOOK_SECRET`
- `RC_WEBHOOK_SECRET`
- `APPLE_WEBHOOK_SECRET` (we also verify the JWS signature against Apple's root cert)
- `GOOGLE_WEBHOOK_SECRET`

A webhook that fails signature verification is logged and **rejected with 401** (not 400, so we don't leak why).

## Why we accept both RevenueCat AND Apple/Google webhooks

RevenueCat forwards Apple/Google events to us. So we get the same event twice: once from RevenueCat (the wrapper), once from the original (Apple/Google direct).

We treat **RevenueCat as the source of truth for VIP state** (it's easier to maintain, one integration). The direct Apple/Google webhooks are a **backup** for the rare case RevenueCat is down, and they're the **only** source of refunds (RevenueCat doesn't always forward refunds in real time).

In practice: RevenueCat handles VIP, direct handles refunds. The code is written to handle either, with the rule "first writer wins, second is a no-op."

## Webhook reliability

- All webhooks return 202 within 200ms.
- Long work is enqueued via `BackgroundTasks` (FastAPI built-in) or pushed to RQ (Redis Queue) for heavier work.
- If a webhook handler crashes, the provider retries (Apple/Google retry up to 5 times over 24h; RevenueCat retries for 3 days).
- Idempotency keys are stored for 30 days; we never process the same event twice.

## What we do NOT do via webhooks

- ❌ Send push notifications (we queue them, but the actual APNs/FCM call is from a separate worker, not the webhook handler).
- ❌ Trigger emails (same — queued, not inline).
- ❌ Recompute analytics (the periodic cron does this on a schedule, not reactively).
