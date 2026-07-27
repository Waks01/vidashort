# Content endpoints

Series, episodes, streaming. Read-mostly public, with entitlement gating on stream URLs.

## Conventions

- Series slugs are kebab-case and unique: `"the-ceos-forbidden-bride"`.
- `category` ∈ the genre enum (see `MockData.genres`): `romance`, `ceo`, `revenge`, `werewolf`, `billionaire`, `marriage`, `fantasy`, `thriller`, `family`, `historical`, `other`.
- `source` ∈ `{"original", "tmdb", "creator"}`.
- `language` ∈ the supported set: `en`, `yo`, `ig`, `ha`, `fr`. Defaults to `en`.
- `cover_url` is a CF Stream or TMDB image, served via our CDN. Always `https://`.

## Endpoints

### GET /v1/content/series

- **Auth:** public
- **Query:** `?cursor=<opaque>&limit=20&category=<genre>&source=<src>&q=<text>&language=<iso>`
- **Response 200:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "slug": "the-ceos-forbidden-bride",
        "title": "The CEO's Forbidden Bride",
        "synopsis": "He married her to save his empire. He never expected to fall...",
        "coverUrl": "https://cdn.vidashort.app/posters/...",
        "backdropUrl": "https://cdn.vidashort.app/backdrops/...",
        "category": "romance",
        "language": "en",
        "source": "tmdb",
        "tags": ["ceo", "marriage", "enemies-to-lovers"],
        "totalEpisodes": 60,
        "freeEpisodes": 3,
        "isVipOnly": false,
        "rating": 4.6,
        "createdAt": "2026-06-01T00:00:00Z"
      }
    ],
    "nextCursor": "eyJsYXN0SWQiOiJhYmMifQ=="
  }
  ```
- **Notes:** Default sort is `total_episodes DESC, created_at DESC`. Home page uses this with `?category=<user's genres>`.

### GET /v1/content/series/{slug}

- **Auth:** public
- **Response 200:**
  ```json
  {
    "series": { ...same as list item... },
    "episodes": [
      {
        "number": 1,
        "title": "The Wedding That Wasn't",
        "synopsis": "Vivian stands at the altar in a dress that isn't hers...",
        "durationS": 92,
        "requiredCoins": 0,
        "isFree": true,
        "thumbnailUrl": "https://..."
      }
    ]
  }
  ```
- **Errors:** `404 series_not_found`.
- **Notes:** The `episodes` array is metadata only. The actual `playbackUrl` comes from the next endpoint.

### GET /v1/content/series/{slug}/episodes/{n}/stream

- **Auth:** optional (anonymous gets a 403 paywall too, but we never call this anonymously — the player always has a user)
- **Response 200 (entitled):**
  ```json
  {
    "episodeId": "uuid",
    "playbackUrl": "https://customer-...cloudflarestream.com/{uid}/manifest/video.m3u8?...",
    "expiresAt": "2026-07-22T12:00:00Z",
    "captionsUrl": "https://...",
    "prerollAd": null,
    "midrollAtS": null,
    "posterUrl": "https://..."
  }
  ```
- **Response 403 (paywall required):**
  ```json
  {
    "error": "entitlement_required",
    "message": "Unlock this episode to keep watching",
    "details": {
      "paywall": {
        "path": "coins",
        "costCoins": 25,
        "rewardCoins": 0,
        "remainingAds": 96,
        "label": "Use 25 coins"
      }
    }
  }
  ```
- **Errors:**
  - `404 episode_not_found`
  - `403 entitlement_required` (with `details.paywall`)
  - `403 series_country_blocked` (Phase 4 — geo restrictions)
- **Notes:**
  - `playbackUrl` is signed, 1h TTL. Client must re-fetch (not cache beyond expiry).
  - `prerollAd` is null if user is VIP, else served from ad decisioning.
  - `midrollAtS` is null if user is VIP, else the timestamp the player should pause for an in-player ad.
  - This is the only endpoint the player calls. Everything else is metadata.
  - Calling this increments `watch_history` (position 0, completed false). Subsequent re-fetches don't increment.

### POST /v1/content/{seriesId}/favorite

- **Auth:** required
- **Response 204**
- **Notes:** Idempotent. Favoriting twice is fine.

### POST /v1/content/{seriesId}/unfavorite

- **Auth:** required
- **Response 204**

### GET /v1/content/featured

- **Auth:** public
- **Response 200:**
  ```json
  {
    "items": [
      { "episodeId": "uuid", "seriesId": "uuid", "slot": "hero", "order": 0 },
      { "episodeId": "uuid", "seriesId": "uuid", "slot": "card", "order": 1 },
      { "episodeId": "uuid", "seriesId": "uuid", "slot": "sponsored", "order": 2, "sponsor": "Acme VPN" }
    ]
  }
  ```
- **Notes:**
  - This is the curated home feed. The mobile app calls this first, then resolves episode metadata.
  - Order is admin-controlled via the "Feature on home" admin action.
  - "Sponsored" slots inject every 6th item by convention, but the slot is explicit, not implicit.

## Shapes

```ts
type Series = {
  id: string;
  slug: string;
  title: string;
  synopsis: string;
  coverUrl: string;
  backdropUrl: string;
  category: string;
  language: string;
  source: "original" | "tmdb" | "creator";
  creatorId: string | null;
  tags: string[];
  totalEpisodes: number;
  freeEpisodes: number;     // first N free
  isVipOnly: boolean;
  rating: number;           // 0–5
  createdAt: string;
};

type EpisodeMeta = {
  number: number;
  title: string;
  synopsis: string;
  durationS: number;
  requiredCoins: number;
  isFree: boolean;
  thumbnailUrl: string;
};

type StreamResponse = {
  episodeId: string;
  playbackUrl: string;
  expiresAt: string;
  captionsUrl: string | null;
  prerollAd: { adId: string; durationS: number } | null;
  midrollAtS: number | null;
  posterUrl: string;
};

type PaywallDecision = {
  path: "vip" | "coins" | "ad" | "premium";
  costCoins: number;
  rewardCoins: number;       // 20 if path === "ad", else 0
  remainingAds: number;       // 0–100, only meaningful if path === "ad"
  label: string;              // pre-rendered CTA text
};
```
