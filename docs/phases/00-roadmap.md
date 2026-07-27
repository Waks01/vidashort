# Roadmap

What we're building, in what order, with verification gates between each phase.

## Locked economics

| Value | Number |
|---|---|
| 10 coins = ₦1 | locked |
| 25 coins per episode unlock | locked |
| 20 coins per rewarded ad | locked |
| 100 ads/day user cap | locked |
| 60% creator / 40% platform split | locked |
| ₦5,000 (50,000 coins) min creator payout | locked |
| Paywall decision order: VIP → coins → ad → premium | locked |
| 17+ age gate | locked |
| Currency display: Naira (₦) | locked |
| Payout methods: OPay, PalmPay, Moniepoint, Bank | locked |

## Locked product rules

- Paywall is dismissable (App Store rule). Close X always works.
- Refunds are honoured. We never claw back content.
- Age gate is enforced before the first ad.
- No data sharing with third parties beyond what's required for ads + IAP.
- The home feed is personalised to the user's genre selection after onboarding.
- Daily reward is 7-day streak; day 7 is a "jackpot" 50 coins.

## Phase 0 — Setup

- Repo init, `.gitignore`, basic structure.
- OneDrive exclusion runbook.
- Brand decision: 3D V-Forward wordmark + 3D Play-V app icon (locked).
- Token system: `apps/design/styles/tokens.css`.

## Phase 0.5 — Visual prototype ✅ COMPLETE

**Status:** Done. 43 screens, 4 CSS files, 3 JS files, ~ 6000 lines.

**What's there:**
- All pre-auth screens (splash, onboarding, genre-picker, role-picker, age-gate, auth-entry, creator-signup, sign-up, sign-in, forgot-password, otp).
- All main app screens (home feed, discover, search, series detail, episode player, comments, share).
- All money screens (library, wallet, coin store, VIP, daily reward, paywall, rewarded ad, interstitial).
- All system screens (profile, settings, notifications).
- All state screens (empty, error, loading).
- All creator screens (dashboard, series, upload, analytics, payouts).
- All admin screens (overview, moderation, content, users, ads, finance).
- Role-aware bottom nav (viewer / creator / admin).
- Shared chrome script (`scripts/chrome.js`).
- 3 marquee screens polished (home, player, paywall).
- Index landing page with locked-economics panel.

**Known bug fixed in this phase:** `apps/design/scripts/app.js` line 320 was clobbering `MockData` from `data.js`. Fixed by merging with `Object.assign`.

**Verification:** Open `apps/design/index.html` in a browser. Every screen renders. Every CTA leads somewhere. No console errors. localStorage state persists across reloads.

**Not done:** the visual prototype is read-only from this point on. Future changes go to the design system in `docs/brand/` and the live mobile app.

## Phase 1 — Expo mobile skeleton

**Status:** next. See `docs/phases/01-mobile-skeleton.md`.

**Goal:** A runnable Expo app that boots, shows splash + onboarding, and renders the home feed against a mock API. No real backend. No real IAP. No real video. But the screens, gestures, and design tokens work.

**Builds:**
- Move `mobile/` into `apps/mobile/`. Workspace setup.
- `packages/shared/` with zod schemas.
- Design system in TS (`lib/theme/tokens.ts`).
- `(auth)/` route group: splash → onboarding → genre-picker → age-gate → role-picker → auth-entry → sign-up → sign-in.
- `(viewer)/` route group: home (mocked), discover (mocked), library (mocked), wallet (mocked), profile.
- Mock API client (`lib/api/`) that returns the same shapes as the real backend, backed by a hardcoded `MockData` mirror of `apps/design/scripts/data.js`.
- Bottom nav with role-aware tabs.
- expo-router typed routes.
- OneDrive exclusion set up by the user (per runbook).

**Verification:** `npm run mobile` → Expo dev server starts. iOS simulator launches. Splash shows, advances to onboarding, swipe through 3 slides, genre-picker allows selection, age-gate confirms, role-picker routes to sign-up. Sign up → home feed shows 12 mocked episodes. Tap one → player (still mocked with the gradient). No console errors.

## Phase 1.5 — Build + distribution

**Status:** after Phase 1.

**Goal:** A TestFlight build and a Play internal track build, installable on real devices.

**Builds:**
- EAS Build profiles: development, preview, production.
- App icon, splash, app.json configured for stores.
- Privacy policy, support URL, age rating.
- TestFlight: create app, upload first build, internal testers.
- Play Console: create app, upload first AAB, internal track.
- Sentry project + SDK wired in mobile.

**Verification:** User installs TestFlight build on their iPhone. User installs internal track APK on their Android. Both boot to the home feed.

## Phase 2 — FastAPI backend skeleton

**Status:** after Phase 1.5.

**Goal:** A FastAPI service that handles sign-up, sign-in, refresh, and `/v1/me`. End-to-end with a real Postgres + Redis. Mobile calls the real API (instead of the mock).

**Builds:**
- `apps/api/` skeleton.
- Pydantic Settings, JWT, bcrypt.
- SQLAlchemy 2 async models for `users`, `user_identities`, `refresh_tokens`.
- Alembic migrations.
- `docker-compose.yml` for local Postgres + Redis.
- Fly.io app created (no deploy yet).
- Neon Postgres project created.
- Upstash Redis created.
- Sentry project + SDK wired in API.
- Neon + Upstash creds in `.env` (per-developer, gitignored).
- Mobile app points `EXPO_PUBLIC_API_URL` to the staging URL.

**Verification:** Sign up on the mobile app → row in Neon `users`. Sign in → JWT + refresh. Refresh → new pair. `/v1/me` returns the right balance. End-to-end from mobile, no mocks.

## Phase 2.5 — Real auth + content

**Status:** after Phase 2.

**Goal:** Sign in with Apple + Google actually work. Real content catalog (seeded from TMDB) renders on the home feed. Cloudflare Stream URLs work in the player.

**Builds:**
- Apple Developer config (Service ID, key, JWT signing).
- Google Cloud config (OAuth client, ID token verify).
- TMDB API key, seed script (3 originals × 10 episodes).
- Cloudflare Stream account, signed upload + playback URLs.
- Watch history, favorites, series list, episode list (real DB, not mock).

**Verification:** Sign in with Apple on a real iPhone → VIP state correct. Sign in with Google on a real Android. The home feed shows 3 seeded series with real TMDB posters. Tap an episode → video plays (via Cloudflare Stream, even if it's a 5-second test clip).

## Phase 3 — Paywall, coins, ads

**Status:** after Phase 2.5.

**Goal:** The paywall works end-to-end. Real IAP via RevenueCat. Real rewarded ads via AppLovin MAX. Creator upload + earnings work.

**Builds:**
- `services/paywall.py` with the locked decision order, every path tested.
- `services/ad_cap.py` with Redis.
- RevenueCat integration (mobile SDK + server webhook).
- AppLovin MAX integration (mobile SDK + S2S callback).
- Creator flow: upload series + episodes, submit for review, see earnings.
- Admin moderation: approve / reject.
- Coin packs in App Store Connect + Play Console.

**Verification:** Fresh user signs up, lands on home feed. Taps episode 4 (first paywalled). Paywall opens. User taps "Watch ad". AppLovin serves an ad (test mode in dev). Coins credited. User can now play. Admin approves a creator's series. Creator sees earnings. Creator cashes out via OPay (manual transfer by admin). Payout marked paid.

## Phase 4 — Polish, comments, share, library, notifications

**Status:** after Phase 3.

**Goal:** The app feels finished. No rough edges. Real comments, share, library tabs, push notifications.

**Builds:**
- Comments with replies, like, soft delete.
- Share sheet (system share via `expo-sharing`).
- Library tabs: Continue Watching, Favorites, Watchlist, History.
- Push notifications via Expo Notifications + a server-side worker.
- Settings: language, genres, notifications, sign out, delete account.
- Search: real Postgres full-text search.
- Discover: real recommendation algorithm.
- Empty / error / loading states polished on every screen.
- Animations + haptics on every interaction.

**Verification:** All 43 prototype screens have a real mobile equivalent. No mock data anywhere. Smoke test on a real device for 30 minutes finds no console errors, no broken states, no 500s.

## Phase 5 — Observability, finance, growth

**Status:** after Phase 4.

**Goal:** We can run this in production. We can see what's happening. We can iterate.

**Builds:**
- Sentry: error tracking, performance monitoring, release tracking.
- PostHog: product analytics (screen views, paywall conversions, ad completion, etc.).
- Admin finance dashboard: real net revenue, ledger, payout decisions.
- Materialised views for daily KPIs.
- Payout automation: integrate with OPay / PalmPay APIs (manual for now, automated in Phase 6).
- Cron jobs: streak reset, payout reminder, content refresh, etc.
- Rate limiting middleware.
- CDN caching for `/v1/content/series`.
- Internationalisation: Yoruba, Igbo, Hausa, French.

**Verification:** Live for 1 week with 1000+ daily active users. No Sentry errors above `info`. Admin sees accurate KPIs. Payout requests get approved within 48h. Coin balance is correct for 100% of users.

## Phase 6 — Beyond (deferred)

- ❌ Offline downloads for VIP.
- ❌ Live comments.
- ❌ AI recommendations (CF-based or LLM-based).
- ❌ Creator collabs.
- ❌ Live events (creator premieres).
- ❌ Multi-language audio dubs.
- ❌ Cross-app sharing to TikTok / Instagram Reels.

## Critical-path rules

- **No phase starts until the previous phase's verification passes.**
- **No new dependencies without a written reason** (see `docs/steering/00-rules.md`).
- **No changes to locked numbers without user approval.**
- **No money flows without end-to-end verification on a real device.**
- **No deploy on a Friday.** (Real rule. Friday deploys age badly.)

## How to read the phase specs

Each `docs/phases/0X-*.md` file has the same structure:

```
# Phase X — name

## Goal
One-sentence outcome.

## Why this order
Why this phase precedes the next.

## What's in scope
Concrete deliverables. Files to create, components to build, tests to write.

## What's out of scope
Explicitly NOT in this phase. Defer to a later phase.

## Tasks
Numbered, ordered, each with:
  - File to edit
  - What the change is
  - How to verify it's done
  - Approx lines of code

## Verification
End-to-end smoke test. Real device or local curl. Pass/fail criteria.

## Hand-off
What the next phase assumes is in place. The next phase spec depends on this.
```

If a task in a phase seems too small to be a deliverable, it goes in a sub-bullet. If it seems too big, it splits into two phases.
