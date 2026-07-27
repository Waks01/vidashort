# Phase 3 — Paywall, coins, ads, creator

## Goal

The full monetisation loop. Users can buy coins, watch rewarded ads, pay for episodes, and creators can upload, get approved, earn, and cash out. This is the phase that makes money.

## Why this order

We have to have the auth + content spine (Phases 1, 2, 2.5) before we can charge for content. Once that's solid, the paywall is the highest-leverage work because it directly drives revenue.

## What's in scope

### 1. The paywall service (Day 1-2)

- `app/services/paywall.py` with `decide()` and `pay_with_coins()`, `pay_with_ad()`, `pay_with_vip()`.
- The decision order is **locked** in `CLAUDE.md` and `docs/api/04-entitlement.md`. Order: VIP → free → coins → ad → premium.
- `app/routers/entitlement.py` with `POST /v1/entitlement/check`, `POST /v1/entitlement/unlock`.
- `app/services/revenue_split.py` with `credit_creator(creator_id, gross_coins)` — implements the 60/40 split atomically with the user's debit.
- `app/db/models/coin_txn.py` — the append-only ledger.
- `app/db/models/creator_earning.py` — 60% credit per unlock.

This is the most important service in the product. **Every code path is tested.**

### 2. Ad cap service (Day 2)

- `app/services/ad_cap.py` with `today_key(user_id)`, `remaining(user_id)`, `record(user_id, ad_id)`.
- Redis-backed. INCR + EXPIRE. UTC midnight reset.
- Postgres `ad_impressions` table for the durable record.
- `app/routers/ads.py` with `GET /v1/ad/cap`, `POST /v1/ad/record`.

### 3. Coins / IAP (Day 3-4)

- `app/routers/coins.py` with `GET /v1/coins/balance`, `GET /v1/coins/packs`, `POST /v1/coins/purchase`.
- `app/integrations/apple.py` — App Store Server API v2 receipt verification.
- `app/integrations/google.py` — Play Developer API purchase verification.
- `app/integrations/revenuecat.py` — RevenueCat REST API for VIP verification.
- `app/routers/webhooks.py` with `POST /v1/webhooks/apple`, `POST /v1/webhooks/google`, `POST /v1/webhooks/revenuecat`.
- All webhooks: signature verification + idempotency.

### 4. Mobile IAP (Day 3-4)

- `apps/mobile/src/lib/iap/revenuecat.ts` — `react-native-purchases` wrapper.
- `apps/mobile/src/lib/iap/use-purchase.ts` — React hook with the purchase flow.
- `apps/mobile/src/app/(viewer)/coin-store.tsx` — 5 packs, Best Value badge, processing + success states.
- `apps/mobile/src/app/(viewer)/paywall.tsx` — modal route, dismissable, 3 CTAs.
- `apps/mobile/src/app/(viewer)/vip.tsx` — Monthly/Yearly toggle, comparison table, "Start Free Trial".
- `apps/mobile/src/app/(viewer)/daily-reward.tsx` — 7-day streak, claim animation, confetti.
- `apps/mobile/src/app/(viewer)/wallet.tsx` — coin balance, transactions, daily check-in banner.
- `apps/mobile/src/components/paywall-modal.tsx` — the modal that opens when the paywall decision is `path != 'vip'`.
- `apps/mobile/src/components/confetti.tsx` — `react-native-reanimated` worklets.
- `apps/mobile/src/components/toast.tsx` — bottom toast with variants.
- `apps/mobile/src/components/confirm.tsx` — destructive confirm.

### 5. Mobile ads (Day 5)

- `apps/mobile/src/lib/monetization/ad-cap.ts` — mirrors server cap in MMKV.
- `apps/mobile/src/lib/monetization/rewarded-ad.ts` — AppLovin MAX wrapper, S2S callback to `/v1/ad/record`.
- `apps/mobile/src/components/sponsored-card.tsx` — in-feed sponsored drama.
- `apps/mobile/src/components/ad-banner.tsx` — bottom banner.
- `apps/mobile/src/app/(viewer)/26-rewarded-ad.tsx` — 3 states (loading / playing / complete).
- `apps/mobile/src/app/(viewer)/27-interstitial-ad.tsx` — full-bleed with 5s countdown.

### 6. Creator (Day 6-8)

- `app/routers/creator.py` with the full creator surface.
- `app/integrations/cloudflare_stream.py` — signed upload + playback URLs.
- `app/db/models/series.py`, `episodes.py` — full content schema.
- `app/services/moderation.py` — auto-flag keywords.
- `app/routers/admin.py` with `POST /v1/admin/moderation/{id}/decide`.
- `app/services/coins.py` — credit / debit / ledger.
- `app/db/models/payout_request.py` — the payout queue.

### 7. Mobile creator (Day 7-8)

- `apps/mobile/src/app/(creator)/dashboard.tsx` — earnings, KPIs, quick actions.
- `apps/mobile/src/app/(creator)/series/index.tsx` — list with status badges.
- `apps/mobile/src/app/(creator)/series/new.tsx` — upload form: poster drop, title/synopsis, episode list editor, language/tags.
- `apps/mobile/src/app/(creator)/analytics.tsx` — 30-day chart, by-series breakdown.
- `apps/mobile/src/app/(creator)/payouts.tsx` — balance, cashout button, history.
- `apps/mobile/src/app/(creator)/account.tsx` — channel profile, payout method.

### 8. Mobile admin (Day 8-9)

- `apps/mobile/src/app/(admin)/overview.tsx` — platform KPIs.
- `apps/mobile/src/app/(admin)/moderation.tsx` — 3-tab queue, approve/reject.
- `apps/mobile/src/app/(admin)/content.tsx` — all series, search/filter.
- `apps/mobile/src/app/(admin)/users.tsx` — search, filter, view.
- `apps/mobile/src/app/(admin)/ads.tsx` — campaigns, pause/resume.
- `apps/mobile/src/app/(admin)/finance.tsx` — net revenue, ledger, payout decisions.

### 9. The episode player (Day 9-10)

- `apps/mobile/src/app/(viewer)/episode/[id].tsx` — full-bleed 9:16.
- `apps/mobile/src/lib/video/player.ts` — `expo-video` wrapper, gesture handling, mid-roll, pre-roll.
- `apps/mobile/src/components/video-item.tsx` — the feed slide (already from Phase 1, but the tap-to-play behaviour is wired here).

### 10. Tests (Day 10)

- `tests/test_entitlement.py` — **every** path through `paywall.decide()` is tested. The 4 paths × 2 outcomes (entitled / denied) = 8+ test cases.
- `tests/test_coins.py` — purchase, balance, refund, idempotency.
- `tests/test_ads.py` — cap, record, 429.
- `tests/test_creator.py` — upload, submit, earnings, payout.
- `tests/test_admin.py` — moderation, payout decisions.
- `tests/test_webhooks.py` — signature verification, idempotency.

## What's out of scope

- ❌ Live comments (Phase 4).
- ❌ Share, library, history (Phase 4).
- ❌ Push notifications (Phase 4).
- ❌ Production deploy (Phase 5).
- ❌ Observability / Sentry dashboards (Phase 5).
- ❌ PostHog / product analytics (Phase 5).
- ❌ Internationalisation (Phase 5).

## Tasks (ordered, with line estimates)

1. **Paywall service** — `services/paywall.py`, `revenue_split.py`, `coins.py`. **~ 600 lines.**
2. **Entitlement router** — `routers/entitlement.py`, schemas. **~ 200 lines.**
3. **Ad cap service** — `services/ad_cap.py`. **~ 150 lines.**
4. **Ads router** — `routers/ads.py`, schemas. **~ 200 lines.**
5. **DB models** — `coin_txn.py`, `creator_earning.py`, `ad_impression.py`, `payout_request.py`, `series.py`, `episodes.py`. **~ 500 lines.**
6. **Migrations** — 6 new alembic files. **~ 600 lines.**
7. **Coin router + IAP integrations** — `routers/coins.py`, `integrations/apple.py`, `integrations/google.py`, `integrations/revenuecat.py`. **~ 800 lines.**
8. **Webhooks router** — `routers/webhooks.py`. **~ 400 lines.**
9. **Creator router + service** — `routers/creator.py`, `services/moderation.py`, `integrations/cloudflare_stream.py`. **~ 800 lines.**
10. **Admin router** — `routers/admin.py`, schemas. **~ 600 lines.**
11. **Mobile paywall + IAP** — `lib/iap/*`, `lib/monetization/*`, `app/(viewer)/{paywall,coin-store,vip,daily-reward,wallet}.tsx`, components. **~ 2,000 lines.**
12. **Mobile ads** — `lib/monetization/*`, `app/(viewer)/{rewarded-ad,interstitial-ad}.tsx`. **~ 500 lines.**
13. **Mobile creator** — `app/(creator)/*`, 6 route files. **~ 1,500 lines.**
14. **Mobile admin** — `app/(admin)/*`, 6 route files. **~ 1,200 lines.**
15. **Mobile player** — `lib/video/player.ts`, `app/(viewer)/episode/[id].tsx`, gesture handling. **~ 800 lines.**
16. **Tests** — `tests/test_*.py`. **~ 2,000 lines.**

Total: **~ 12,000 lines of new code.** This is the biggest phase by code volume AND the most important by revenue.

## Verification

The end-to-end smoke test (run on a real device, real money disabled):

1. Fresh user signs up. Lands on home feed. Sees 3 series.
2. Taps episode 1 (free). Plays.
3. Completes episode 1. Episode 2 (paywalled) is up next.
4. Taps play. Paywall modal opens with "Use 25 coins" as the primary CTA.
5. User has 0 coins, so they tap "Watch ad". AppLovin MAX test ad plays. Completes. +20 coins.
6. Now has 20 coins. Taps "Use 25 coins" again. Insufficient. Toast.
7. Taps "Watch ad" again. +20 coins. Now has 40.
8. Taps "Use 25 coins". Spends 25. Now has 15. Paywall closes. Episode 2 plays.
9. Pulls up the wallet. Balance shows 15. Lifetime earned 40. Lifetime spent 25. Transactions: "unlock -25, rewarded_ad +20, rewarded_ad +20".
10. Goes back to home. Episode 3. Taps play. Paywall. Taps X (dismissable). Returns to home.
11. Creator flow: separate user, signs up as creator. Channel "Test Drama". Payout method OPay. Submits a series "My Drama" with 1 episode (uploads a real test video file to Cloudflare Stream).
12. Cloudflare webhook fires. Video is `ready`. Series status flips to `pending`.
13. Admin (third user) signs in, opens moderation queue. Sees "My Drama" pending. Approves.
14. Series is published. Original viewer's home feed now shows 4 series.
15. Original viewer watches 1 episode of "My Drama". 25 coins spent. 15 (60%) credits to creator.
16. Creator opens dashboard. Earnings: 15 coins (₦1.50). Pending.
17. Creator submits payout request: 50000 coins. **Below minimum**, error.
18. Creator keeps watching. (Skip ahead.) After enough unlocks, pending hits 50000.
19. Creator submits payout. Status: `pending`. Balance deducted.
20. Admin opens finance. Sees pending payout. Approves.
21. Admin transfers via OPay (manual). Marks paid.
22. Creator's payout history shows "Paid ₦5,000".
23. **Check Postgres `coin_txn`:** every transaction has a row, all balance_afters are correct, no negative balances.
24. **Check Postgres `creator_earnings`:** every creator credit is 60% of the gross.
25. **Check Redis:** ad cap counter = 2 (matches the 2 ads watched today).

**Pass criteria:**
- Every step completes without errors.
- The DB ledger is correct (spot-check 5 random rows).
- The creator's pending balance matches `SUM(creator_earnings) - SUM(payouts approved/paid)`.
- No Sentry errors above `info`.
- No 4xx / 5xx on the API logs (except the expected `409 already_unlocked` and `400 below_minimum`).

## Hand-off

What Phase 4 (polish) assumes:
- The paywall is the source of truth for monetisation.
- All money is in the ledger, never on a balance alone.
- The creator + admin stacks are functional.
- The player is real (expo-video, real stream URL).
- IAP is real (RevenueCat + Apple/Google).

What Phase 5 (observability) assumes:
- Money flows have a clear audit trail.
- Sentry catches the expected classes of errors (none in the happy path).
- Admin can see the platform's KPIs.
