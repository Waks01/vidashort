# Admin endpoints

Platform-wide operations. Auth: `role: "admin"`.

## Conventions

- All endpoints require `role: "admin"`. A regular creator or viewer gets `403 admin_only`.
- Every admin action writes to `audit_log` with `actor_id`, `action`, `target_kind`, `target_id`, `before`, `after`.
- Money is read in Naira for display, written in coins. Admin actions on money always use coins.
- Payouts and refunds are **two-step**: admin clicks "Approve", which marks the request `approved`; a separate manual transfer (out of band) marks it `paid`. The "paid" state is set by the admin after they transfer via OPay/PalmPay/etc.

## Endpoints

### GET /v1/admin/overview

- **Auth:** admin
- **Query:** `?range=24h | 7d | 30d | 90d`
- **Response 200:**
  ```json
  {
    "gmvNaira": 1240000,
    "netRevenueNaira": 124000,
    "dau": 18400,
    "mau": 142000,
    "newSignups": 1200,
    "payingUsers": 4200,
    "activeVip": 850,
    "adCapHits": 320,
    "moderationQueueSize": 18,
    "pendingPayoutsNaira": 85000,
    "topSeries": [
      { "seriesId": "uuid", "title": "The CEO's...", "views": 240000 }
    ]
  }
  ```
- **Notes:**
  - `gmvNaira` = gross merchandise value (sum of all coin purchases in the period, in Naira).
  - `netRevenueNaira` = `gmvNaira * 0.7` (after store fee) - creator share - refunds.
  - `dau` / `mau` from `watch_history` unique users in the period.
  - `activeVip` = users with non-expired `vip_entitlements`.
  - `adCapHits` = users who hit the 100-ads-per-day cap yesterday.
  - `moderationQueueSize` = `moderation_items` with `status: "pending"`.

### GET /v1/admin/moderation

- **Auth:** admin
- **Query:** `?kind=series|comment|account&status=pending&cursor=&limit=20`
- **Response 200:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "kind": "series",
        "refId": "series-uuid",
        "title": "My Drama",
        "submittedBy": "creator-name",
        "submittedAt": "2026-07-22T10:00:00Z",
        "reason": "Auto-flagged: contains 'XXX'",
        "preview": { ... }
      }
    ],
    "nextCursor": "..."
  }
  ```
- **Notes:**
  - `series` items include a `preview` with the cover, synopsis, first 3 episode metadata.
  - `comment` items include the comment text and the parent episode.
  - `account` items include the user's profile and recent activity.

### POST /v1/admin/moderation/{id}/decide

- **Auth:** admin
- **Request:** `{ "decision": "approve" | "reject", "note": "Looks fine, releasing." }`
- **Response 200:** updated item.
- **Side effects:**
  - `series` + `approve`: `series.is_published = true`, `series.moderation_status = "approved"`. Series goes live.
  - `series` + `reject`: `series.moderation_status = "rejected"`, `series.is_published = false`. Creator gets a notification.
  - `comment` + `approve`: comment stays visible.
  - `comment` + `reject`: `comment.deleted_at = now()`, comment text replaced with "[removed]".
  - `account` + `approve`: user is unbanned.
  - `account` + `reject`: `user.banned_at = now()`, all sessions invalidated.
- **Audit:** every decision is logged with `before` and `after` snapshots.

### GET /v1/admin/content

- **Auth:** admin
- **Query:** `?cursor=&source=&q=&category=&moderationStatus=`
- **Response 200:** same shape as `GET /v1/content/series` but unfiltered, includes `is_published`, `moderation_status`, `creator_id`.

### PATCH /v1/admin/content/{id}

- **Auth:** admin
- **Request (any subset):**
  ```json
  {
    "isPublished": false,
    "moderationStatus": "rejected",
    "title": "...",
    "synopsis": "...",
    "tags": ["..."]
  }
  ```
- **Response 200:** updated series.
- **Side effects:** audit log.

### POST /v1/admin/content/{id}/feature

- **Auth:** admin
- **Request:** `{ "slot": "hero" | "card" | "sponsored", "order": 0 }`
- **Response 200:** updated featured entry.
- **Side effects:** audit log. Mobile `/v1/content/featured` returns the new order.

### GET /v1/admin/users

- **Auth:** admin
- **Query:** `?cursor=&role=&q=&banned=true|false`
- **Response 200:** paginated user list with summary stats (coins, vip, last seen).

### GET /v1/admin/users/{id}

- **Auth:** admin
- **Response 200:** full user detail + last 50 transactions + watch history summary.

### PATCH /v1/admin/users/{id}

- **Auth:** admin
- **Request (any subset):**
  ```json
  {
    "role": "creator",
    "banned": true,
    "banReason": "Spam",
    "refundCoins": 1200
  }
  ```
- **Response 200:** updated user.
- **Side effects:**
  - `role` change: user is signed out everywhere (refresh tokens invalidated). Next sign-in uses the new role.
  - `banned: true`: `banned_at = now()`, all sessions invalidated, user gets `403 user_banned` on every API call.
  - `refundCoins`: adds coins, writes `coin_txn` with `reason: "admin_refund"`, `ref_id: admin_user_id`.

### GET /v1/admin/ads

- **Auth:** admin
- **Response 200:**
  ```json
  {
    "campaigns": [
      {
        "id": "uuid",
        "name": "Acme VPN",
        "network": "appLovin",
        "adUnitId": "...",
        "type": "rewarded" | "interstitial" | "banner",
        "status": "active" | "paused",
        "fillRate": 0.92,
        "ecpmNaira": 12.4,
        "dailyImpressions": 12000,
        "dailyCompletions": 8400,
        "updatedAt": "2026-07-20T00:00:00Z"
      }
    ]
  }
  ```

### PATCH /v1/admin/ads/{id}

- **Auth:** admin
- **Request:** `{ "status": "active" | "paused", "dailyCap": 50000 }`
- **Response 200:** updated campaign.
- **Side effects:** `status: "paused"` removes the ad from the SDK rotation on the next config sync (within 1 min).

### GET /v1/admin/finance

- **Auth:** admin
- **Query:** `?range=7d | 30d | 90d`
- **Response 200:**
  ```json
  {
    "netRevenueNaira": 124000,
    "grossCoinSalesNaira": 1240000,
    "creatorLiabilityNaira": 248000,
    "platformNetNaira": 124000,
    "ledger": [
      {
        "date": "2026-07-22",
        "type": "coin_sale" | "creator_payout" | "refund" | "ad_revenue",
        "amountNaira": 12000,
        "balanceAfter": 124000
      }
    ]
  }
  ```
- **Notes:**
  - `creatorLiabilityNaira` = sum of `creator_earnings` not yet paid out.
  - `platformNetNaira` = what's actually ours after store fees, creator payouts, refunds.
  - The ledger is a denormalised view; the source of truth is `coin_txn` + `creator_earnings` + `payout_requests`.

### POST /v1/admin/payouts/{id}/decide

- **Auth:** admin
- **Request:** `{ "decision": "approve" | "reject", "note": "Sent via OPay" }`
- **Response 200:** updated payout.
- **Side effects:**
  - `approve`: `payout.status = "approved"`, `decided_at = now()`, `decided_by = admin_id`. The admin then manually transfers via OPay/PalmPay/etc. (out of band) and PATCHes again with `status: "paid"`.
  - `reject`: `payout.status = "rejected"`. Creator's pending balance is restored. Creator gets a notification with the reason.
- **Workflow:**
  1. Admin sees payout in `pending`.
  2. Admin clicks "Approve" → state = `approved`.
  3. Admin transfers money via OPay (manual).
  4. Admin clicks "Mark paid" → state = `paid`. (This is a second admin call; in Phase 5 we add a `POST /v1/admin/payouts/{id}/mark-paid`.)

## Audit log

Every admin action writes to `audit_log`:

```json
{
  "id": "uuid",
  "actorId": "admin-uuid",
  "action": "moderation.decide" | "user.ban" | "user.refund" | "payout.approve" | "content.feature" | "...",
  "targetKind": "series" | "comment" | "user" | "payout" | "...",
  "targetId": "uuid",
  "before": { ... },
  "after": { ... },
  "createdAt": "2026-07-22T11:00:00Z"
}
```

`before` and `after` are full JSON snapshots of the affected resource. This is non-negotiable: if we ever have a "who did this" question, the log is the answer. We keep audit rows for 7 years (Phase 5 backup config).

## Why no separate "admin web" app

- Phase 1–4: admin UI lives in the mobile app under the `(admin)/` route group, behind a role switch (Settings → "Switch to admin" or directly from the index).
- Phase 5 (if needed): a small web admin app in `apps/admin/` for bulk operations. Not a priority.

This keeps us from maintaining two frontends while the product is small.
