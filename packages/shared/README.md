# @vidashort/shared

Shared TypeScript types and Zod schemas for the vidashort monorepo.

## Install

```bash
npm install @vidashort/shared
```

## Schemas

| Export | Path | Description |
|---|---|---|
| `User` | `./schemas/user` | Viewer, creator, admin user shape |
| `UserIdentity` | `./schemas/user` | Auth identity link (email, apple, google) |
| `Genre` | `./schemas/series` | Series genre |
| `EpisodeMeta` | `./schemas/series` | Episode metadata with duration, cost, thumbnail |
| `Series` | `./schemas/series` | Series detail with genres, status, view count |
| `PaywallDecision` | `./schemas/paywall` | Entitlement decision (vip, coins, ad, premium) |
| `AdCap` | `./schemas/ads` | Daily ad watch cap with reset time |
| `CoinTxn` | `./schemas/coin` | Coin transaction record |
| `Comment` | `./schemas/comment` | Comment with user, likes, replies |
| `CommentCreate` | `./schemas/comment` | New comment / reply payload |
| `WatchHistory` | `./schemas/watch-history` | Resume position and completion state |
| `Favorite` | `./schemas/favorite` | User favorite reference |
| `PushToken` | `./schemas/device` | Registered push token |
| `DeviceRegister` | `./schemas/device` | Push registration request |
| `NotificationItem` | `./schemas/notification` | In-app notification list item |

## Usage

```ts
import { User, Series, Comment } from "@vidashort/shared";

const validated = User.safeParse(apiResponse.user);
const list = Series.array().parse(apiResponse.series);
```

## Versioning

- `v1.x` follows semver. Mobile pins `^1.x`.
- Breaking schema changes require bumping major.
- Mirror any change here in the backend Pydantic models in `apps/api/app/db/models/` and `apps/api/app/schemas/`.
