# Phase 4 — Polish, comments, share, library, notifications

## Goal

The app feels finished. No rough edges. Real comments, share, library, push notifications. Every prototype screen has a real mobile equivalent.

## Why this order

Phases 1–3 ship the spine. Phase 4 is "the part users notice but don't pay for." Without it, the app feels like a beta. With it, it feels like a product.

## What's in scope

### 1. Comments (Day 1-2)

- `app/routers/content.py` gets `GET /v1/content/episodes/{id}/comments`, `POST /v1/content/episodes/{id}/comments`, `POST /v1/content/comments/{id}/like`.
- `app/db/models/comment.py` — full comment model.
- `apps/mobile/src/app/(viewer)/comments/[episodeId].tsx` — bottom sheet via `react-native-bottom-sheet`.
- `apps/mobile/src/hooks/use-comments.ts` — infinite-scroll pagination.
- `apps/mobile/src/components/comment-row.tsx` — single comment.
- Top/New tabs.
- Replies (1 level deep, no nested).
- Like, soft delete.

### 2. Share (Day 2)

- `apps/mobile/src/app/(viewer)/share.tsx` — bottom sheet.
- `apps/mobile/src/lib/share.ts` — `expo-sharing` wrapper. Copy link, WhatsApp, X, Facebook, Instagram, system share.
- The link is a universal link: `https://vidashort.app/series/{slug}` that opens the app if installed, falls back to a web preview.

### 3. Library (Day 2-3)

- `apps/mobile/src/app/(viewer)/library.tsx` — 4 tabs.
- `apps/mobile/src/hooks/use-watch-history.ts` — backed by `/v1/me/watch-history` (new endpoint, Phase 4).
- `apps/mobile/src/hooks/use-favorites.ts` — backed by `/v1/me/favorites` (new endpoint).
- Each tab has empty state, loading state, error state.
- "Continue Watching" sorts by last `watched_at` DESC, shows resume position.

### 4. Settings (Day 3)

- `apps/mobile/src/app/(viewer)/settings.tsx` — Account, Notifications, Language, Privacy, Terms, Sign Out, Delete Account.
- `apps/mobile/src/app/(viewer)/notifications.tsx` — push notification list (read / unread / dismiss).
- `apps/mobile/src/components/settings-row.tsx` — shared row.

### 5. Push notifications (Day 4-5)

- Backend:
  - `app/db/models/push_token.py` — FCM/APNs tokens per user.
  - `app/routers/devices.py` — `POST /v1/devices/register`, `POST /v1/devices/{id}/unregister`.
  - `app/services/notifications.py` — queue and dispatch.
  - `app/integrations/fcm.py` — Firebase Cloud Messaging.
  - `app/integrations/apns.py` — Apple Push Notification service (via `aioapns`).
  - `app/worker/notifier.py` — Redis-based queue, drained by a worker process.
- Mobile:
  - `apps/mobile/src/lib/notifications.ts` — `expo-notifications` wrapper, token registration.
  - `apps/mobile/src/app/(viewer)/notifications.tsx` — in-app notification center.
- Triggers (Phase 4 minimum):
  - New episode from a favorited series.
  - Creator you've subscribed to publishes.
  - Daily reward reminder (if streak at risk).
  - Payout approved / rejected.
  - Moderation decision on your content.
- Permission is requested **after** a meaningful interaction (e.g. tapping the bell in the top bar), never on app launch.

### 6. Search (Day 5)

- `apps/mobile/src/app/(viewer)/search.tsx` — input, trending tags, recent (MMKV), results.
- `apps/mobile/src/hooks/use-search.ts` — debounced, backed by `/v1/content/series?q=`.
- Postgres `pg_trgm` index on `series.title`, `series.synopsis` (added in a Phase 4 migration).
- Results: 2-col grid, no paywall indicator (this is browsing, not playing).

### 7. Discover (Day 6)

- `apps/mobile/src/app/(viewer)/discover.tsx` — filter chips (All / Trending / New / Romance / CEO / Revenge / Werewolf), 2-col grid.
- `apps/mobile/src/services/recommendations.py` — simple "popular by genre" + "trending this week" algorithm. Phase 5 swaps for a real one.
- Trending = `watch_history.view_count` in last 7 days, top 20.
- New = `series.created_at` in last 7 days, top 20.

### 8. Wallet polish (Day 6)

- `apps/mobile/src/app/(viewer)/wallet.tsx` — coin balance (huge gold), VIP card (if VIP), daily check-in banner, "Earn more" actions, transaction history.
- Animations: coin count-up on receive, confetti on daily claim.
- Transaction list grouped by month.

### 9. State screens (Day 7)

- `apps/mobile/src/components/empty-state.tsx` — shared.
- `apps/mobile/src/components/error-state.tsx` — shared.
- `apps/mobile/src/components/loading-skeleton.tsx` — shared.
- Every screen that fetches data wraps in: loading skeleton → success → error retry.
- The empty / error / loading screens in `apps/design/screens/40-42-*.html` are the pixel reference.

### 10. Polish pass (Day 7-8)

- All animations match the prototype (heart particles, confetti, coin count-up, modal scale-in, sheet slide-up, page transitions).
- Haptics on every primary interaction.
- Accessibility: every interactive element has a label, every screen has a header for screen readers.
- `prefers-reduced-motion` respected: skip the gradient drift on the home feed, disable heart particles.
- All copy proofread. No "lorem ipsum" anywhere.

## What's out of scope

- ❌ Live comments (push updates). Phase 6.
- ❌ WebSocket / SSE.
- ❌ Offline downloads.
- ❌ AI recommendations.
- ❌ Internationalisation.
- ❌ A/B testing framework.
- ❌ Production observability (Sentry + PostHog wired, dashboards in Phase 5).

## Tasks (ordered, with line estimates)

1. **Comments backend** — `models/comment.py`, `routers/content.py` (comment endpoints), `schemas/content.py`. **~ 400 lines.**
2. **Comments mobile** — `comments/[episodeId].tsx`, `use-comments.ts`, `comment-row.tsx`. **~ 600 lines.**
3. **Share mobile** — `share.tsx`, `lib/share.ts`. **~ 200 lines.**
4. **Library** — `library.tsx`, `use-watch-history.ts`, `use-favorites.ts`, `/v1/me/watch-history`, `/v1/me/favorites`. **~ 700 lines.**
5. **Settings + notifications list** — `settings.tsx`, `notifications.tsx`, `settings-row.tsx`. **~ 500 lines.**
6. **Push backend** — `models/push_token.py`, `routers/devices.py`, `services/notifications.py`, `integrations/fcm.py`, `integrations/apns.py`, `worker/notifier.py`. **~ 800 lines.**
7. **Push mobile** — `lib/notifications.ts`, register in `app/_layout.tsx`. **~ 200 lines.**
8. **Search mobile** — `search.tsx`, `use-search.ts`, migration for `pg_trgm` index. **~ 400 lines.**
9. **Discover + recommendations backend** — `services/recommendations.py`, `discover.tsx`. **~ 400 lines.**
10. **Wallet mobile** — `wallet.tsx` polish, transaction grouping, animations. **~ 400 lines.**
11. **State components** — `empty-state.tsx`, `error-state.tsx`, `loading-skeleton.tsx`. **~ 200 lines.**
12. **Polish pass** — animations, haptics, a11y, copy. **~ 400 lines.**

Total: **~ 5,200 lines of new code.**

## Verification

Run the full Phase 4 smoke test on a real device. The criteria:

1. **Comments** — open any episode. Tap the comment icon. Sheet slides up. Top tab shows 5 comments. Tap "+ Post". Type "Great ep!". Submit. Comment appears with my avatar. Tap the like button. Counter increments. Sign out, sign in as another user. Comment still there. Like still there.
2. **Share** — from the player, tap the share icon. Sheet slides up. Tap "Copy link". Toast "Link copied". Open Safari, paste. Universal link works.
3. **Library** — continue watching. Sort by most recent. Resume works (position saved). Favorites tab shows 3 favorited series. Watchlist tab is empty (the design lets users add to watchlist from series detail; verify the entry point).
4. **Settings** — change language to "Yoruba". App re-renders in Yoruba (the strings are in `i18n/yo.json`). Toggle notifications on. Sign out. Confirm modal. Tokens cleared. Returns to splash.
5. **Notifications** — tap the bell in the top bar. The notifications list loads. Mark a notification as read. The unread badge on the bell decreases.
6. **Push** — with notifications enabled, trigger a "new episode" event from the admin (or by manually inserting into the queue). Within 30s, the device receives a push. Tap it. App opens to the new episode.
7. **Search** — type "ceo". Results filter live. Type "zzzzz". Empty state. Clear. Trending tags + recent searches re-appear.
8. **Discover** — filter "Romance". 8 series. Filter "Werewolf". 3 series.
9. **Wallet** — open. Balance animates from 0 to 12,450 (or whatever). Daily check-in banner says "Claim 5 coins" or "Already claimed". Transaction list shows last 20.
10. **States** — turn off Wi-Fi. Open any screen. Loading skeleton appears, then error state with "Retry" button. Tap retry. Toast "No connection".
11. **Polish** — every screen has a back button. Every modal has a close X. Every sheet has a drag handle. The paywall's X works (App Store rule). All animations feel snappy (< 300ms). No console errors.

**Pass criteria:**
- All 11 sections pass.
- No Sentry errors above `warning`.
- All copy is in English (Phase 5 adds i18n).
- `prefers-reduced-motion` is respected (test by enabling it in iOS Settings).

## Hand-off

What Phase 5 (observability) assumes:
- Every screen has a clear loading / success / error state.
- Every state transition is logged.
- All money flows have a clear audit trail.
- The app is feature-complete; what remains is "run it in production."

What Phase 1.5 (build) assumes:
- The app boots, navigates, and renders without metro on a real device.
- All assets are bundled.
- The test app is usable for soft-launch beta testers.
