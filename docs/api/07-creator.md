# Creator endpoints

Upload, manage, and earn from creator content. Auth: `role: "creator"`.

## Conventions

- All endpoints require `role: "creator"` (or `admin`).
- "Creator" is a role on the `users` row, not a separate table. A creator is a user with `role = "creator"`.
- A creator can also have `role = "admin"` (super-user). No conflict.
- Creators cannot unlock their own content (no self-dealing). Enforced in the entitlement service.
- Min payout: 50,000 coins (₦5,000).

## Endpoints

### GET /v1/creator/profile

- **Auth:** creator
- **Response 200:**
  ```json
  {
    "id": "uuid",
    "userId": "uuid",
    "name": "LagosDrama",
    "handle": "lagosdrama",
    "bio": "Telling African love stories, one swipe at a time.",
    "niche": "romance",
    "avatarUrl": "https://...",
    "followerCount": 12400,
    "totalViews": 1840000,
    "payoutMethod": "OPay",
    "payoutAccount": "***1234",
    "payoutAccountName": "Adebayo Okonkwo",
    "verified": true,
    "createdAt": "2026-01-15T00:00:00Z"
  }
  ```

### PATCH /v1/creator/profile

- **Auth:** creator
- **Request (any subset):**
  ```json
  {
    "name": "Lagos Drama",
    "bio": "...",
    "niche": "ceo",
    "payoutMethod": "OPay" | "PalmPay" | "Moniepoint" | "Bank",
    "payoutAccount": "08012345678"
  }
  ```
- **Response 200:** same shape as GET.

### GET /v1/creator/series

- **Auth:** creator
- **Response 200:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "slug": "my-drama-1",
        "title": "My Drama",
        "category": "romance",
        "language": "en",
        "totalEpisodes": 12,
        "moderationStatus": "approved" | "pending" | "rejected" | "draft",
        "isPublished": true,
        "totalViews": 24000,
        "totalUnlocks": 1200,
        "earningsCoins": 18000,
        "earningsNaira": 1800,
        "createdAt": "2026-06-01T00:00:00Z"
      }
    ]
  }
  ```

### POST /v1/creator/series

- **Auth:** creator
- **Request:**
  ```json
  {
    "title": "My New Drama",
    "synopsis": "She came back to Lagos...",
    "category": "romance",
    "language": "en",
    "tags": ["lagos", "second-chance"],
    "totalEpisodes": 10
  }
  ```
- **Response 201:**
  ```json
  {
    "series": { ...same as list item, moderationStatus: "draft" ... },
    "uploadUrls": [
      { "episodeNumber": 1, "videoUploadUrl": "https://...", "coverUploadUrl": "https://..." },
      { "episodeNumber": 2, "videoUploadUrl": "https://..." }
    ]
  }
  ```
- **Side effects:**
  - Creates `series` row with `moderation_status: "draft"`, `is_published: false`, `creator_id: <user>`.
  - Creates N `episodes` rows (one per `totalEpisodes`).
  - Mints signed Cloudflare Stream upload URLs for each episode.
  - Mints signed CF R2 URLs for each cover image.
  - URLs expire in 1h.

### PATCH /v1/creator/series/{id}

- **Auth:** creator (must own the series)
- **Request:** any subset of editable fields.
- **Response 200:** updated series.
- **Notes:** Cannot edit after `moderation_status = "approved"` except `is_published` toggle.

### POST /v1/creator/series/{id}/submit-for-review

- **Auth:** creator (must own the series)
- **Response 200:** series with `moderation_status: "pending"`.
- **Notes:** All episodes must have a `video_uid` (video uploaded + processed). If any is missing, `409 episodes_incomplete`.

### GET /v1/creator/series/{id}/episodes/{n}/upload

- **Auth:** creator (must own the series)
- **Response 200:**
  ```json
  { "videoUploadUrl": "https://...", "expiresAt": "..." }
  ```
- **Notes:** Mints a fresh signed upload URL. Used when the original URL expired or the upload failed.

### GET /v1/creator/analytics

- **Auth:** creator
- **Query:** `?range=7d | 30d | 90d`
- **Response 200:**
  ```json
  {
    "totals": {
      "views": 184000,
      "unlocks": 12400,
      "earningsCoins": 186000,
      "earningsNaira": 18600
    },
    "daily": [
      { "date": "2026-07-15", "views": 12000, "unlocks": 800, "earningsCoins": 12000 }
    ],
    "bySeries": [
      { "seriesId": "uuid", "title": "My Drama", "views": 24000, "unlocks": 1200, "earningsCoins": 18000 }
    ]
  }
  ```

### GET /v1/creator/earnings

- **Auth:** creator
- **Response 200:**
  ```json
  {
    "lifetime": { "coins": 186000, "naira": 18600 },
    "pending": { "coins": 186000, "naira": 18600, "availableForPayout": false },
    "transactions": [
      {
        "id": "uuid",
        "episodeId": "uuid",
        "episodeTitle": "Ep 1: The Wedding",
        "grossCoins": 25,
        "creatorCoins": 15,
        "createdAt": "2026-07-20T10:00:00Z"
      }
    ]
  }
  ```
- **Notes:** `pending` = lifetime minus approved payouts. `availableForPayout` becomes true when `pending.coins >= 50000`.

### POST /v1/creator/payouts

- **Auth:** creator
- **Request:** `{ "amountCoins": 50000 }`
- **Response 201:**
  ```json
  {
    "payout": {
      "id": "uuid",
      "amountCoins": 50000,
      "amountNaira": 5000,
      "status": "pending",
      "payoutMethod": "OPay",
      "payoutAccount": "***1234",
      "requestedAt": "2026-07-22T11:00:00Z"
    }
  }
  ```
- **Errors:**
  - `400 below_minimum` — amountCoins < 50000
  - `400 insufficient_balance` — pending < amountCoins
  - `409 payout_pending` — another payout already in `pending` state; wait for admin
- **Side effects:**
  - Creates `payout_requests` row with `status: "pending"`.
  - Deducts from creator's `pending_coins` (so it can't be double-spent).
  - Admin sees this in the finance dashboard.

### GET /v1/creator/payouts

- **Auth:** creator
- **Response 200:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "amountCoins": 50000,
        "amountNaira": 5000,
        "status": "pending" | "approved" | "rejected" | "paid",
        "payoutMethod": "OPay",
        "requestedAt": "2026-07-22T11:00:00Z",
        "decidedAt": null,
        "decidedBy": null,
        "note": null
      }
    ]
  }
  ```

## Why creators can't unlock their own content

`apps/api/app/services/paywall.py` checks `episodes.series.creator_id != current_user.id` before allowing any unlock. This prevents creators from gaming the system (ranking their own content, inflating earnings).

Self-unlock attempts are logged to `audit_log` for review.

## Why a creator is just a `users.role`

- One account can be viewer + creator. A creator watches other creators' content just like a viewer.
- Switching role requires re-onboarding the creator flow (channel name, payout method).
- Admin role is super-set: admin can do everything a creator can, plus admin endpoints.
- A user can only have one role. Promoting a viewer to creator doesn't remove their viewer access.

## Why 60% to the creator

This is the ReelShort / pocket model. The platform keeps 40% (after the 30% store fee, the actual net is closer to 10–15%, but the headline 60/40 is what creators see and what motivates them to upload).

The split is **only on unlocks**, not on:
- Ad revenue (creators don't get ad share in Phase 1; may revisit in Phase 5+).
- VIP subscription (creators get a share of VIP revenue allocated proportionally to their content's VIP-driven views, computed monthly; Phase 5).
- Daily rewards (creators don't see this).

## What creators see vs what we keep

The creator dashboard shows `earningsCoins` (= 60% of unlock gross). Internally, we also track `grossCoins` (= 100% of unlock gross) for platform net revenue calculation.
