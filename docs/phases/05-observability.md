# Phase 5 — Observability, finance, growth

## Goal

We can run this in production. We can see what's happening. We can iterate.

## Why this order

You can ship Phase 4 and it will work, but you won't know **how well** it's working. Phase 5 turns the app from "a thing that runs" into "a business you can operate."

## What's in scope

### 1. Sentry (Day 1)

- **Mobile:** Sentry React Native SDK wired. Captures JS errors, native crashes, network errors. Release tracking via `X-App-Version`. Sentry source maps uploaded on EAS Build.
- **Backend:** Sentry FastAPI SDK wired. Captures unhandled exceptions, slow queries, 5xx. Profiling enabled.
- **Sourcemaps** generated on every build, uploaded to Sentry.

### 2. PostHog (Day 2)

- **Mobile:** PostHog React Native SDK. Events: `screen_view`, `sign_up`, `sign_in`, `episode_start`, `episode_complete`, `paywall_open`, `paywall_convert`, `ad_watched`, `purchase_attempt`, `purchase_success`, `vip_start`, `share`, `favorite`. Auto-captured: `$pageview`, `$autocapture`.
- **Backend:** PostHog Python SDK for server-side events. Events: `signup_completed`, `first_episode_watched`, `paywall_blocked`, `paywall_converted`, `subscription_started`, `subscription_cancelled`, `payout_requested`, `payout_paid`.
- **Funnels:** signup → first episode → paywall hit → paywall convert. Episode start → episode complete. Purchase attempt → purchase success.

### 3. Admin finance dashboard (Day 2-3)

- `app/routers/admin.py` gets a real `GET /v1/admin/finance` with the ledger.
- `app/services/finance.py` with `daily_revenue(range)`, `creator_liability()`, `platform_net()`.
- `app/db/materialized_views/mv_daily_kpis.sql` — daily KPIs as a materialised view.
- `app/worker/refresh_materialized_views.py` — cron job, every 15 min.
- `apps/mobile/src/app/(admin)/finance.tsx` — full dashboard: net revenue chart, top series, payout queue.

### 4. Admin moderation dashboard (Day 3)

- `apps/mobile/src/app/(admin)/moderation.tsx` — 3 tabs (series, comments, accounts), pull-to-refresh, approve/reject with haptic + toast.
- `app/services/moderation.py` — auto-flag keywords (NSFW, violence, hate speech) using a deny-list (Phase 5; ML in Phase 6).
- Audit log writes on every decision.

### 5. Cron jobs (Day 4)

- `app/worker/cron.py` with:
  - `daily_streak_reset()` — at UTC midnight, mark users who didn't claim yesterday as streak-broken.
  - `daily_revenue_rollup()` — at 1am UTC, compute the previous day's revenue, write to a `daily_revenue` table.
  - `payout_reminder()` — every 6h, email creators with pending payout > 7 days.
  - `content_refresh()` — every 4h, mark `series.rating` from watch_history (rolling avg).
- All jobs idempotent.
- All jobs log to Sentry on failure.
- All jobs visible in `/v1/admin/jobs` (admin only) for debugging.

### 6. Rate limiting (Day 4)

- `app/core/rate_limit.py` — Redis-based, per-user / per-IP buckets.
- Applied to: `POST /v1/auth/signin` (5/10min), `POST /v1/coins/purchase` (10/min), `POST /v1/entitlement/unlock` (10/min), `POST /v1/creator/payouts` (5/day).
- Returns `429 rate_limited` with `Retry-After` header.

### 7. CDN caching (Day 5)

- Cloudflare in front of the API.
- `GET /v1/content/series` and `GET /v1/content/series/{slug}` cached at the edge for 5 min.
- `GET /v1/coins/packs` and `GET /v1/vip/plans` cached for 1 h.
- Everything else: not cached, hits origin.
- Cache keys: include the language param.

### 8. Internationalisation (Day 5-6)

- 5 languages: English (default), Yoruba, Igbo, Hausa, French.
- `apps/mobile/src/i18n/{en,yo,ig,ha,fr}.json` — every user-facing string.
- `apps/mobile/src/lib/i18n.ts` — `useT(key)` hook.
- RTL not in scope (none of these languages are RTL).
- Date / number formatting via `Intl.DateTimeFormat` and `Intl.NumberFormat`.
- All API English text (synopses, series titles) is in English; we don't translate content, just the chrome.

### 9. Production deploy (Day 6-7)

- Fly.io: `vidashort-api-prod` app, autoscale 2–6 instances, deploy via `fly deploy`.
- Neon: `vidashort-prod` project, scale up from 0.5 GB to 2 GB when traffic justifies.
- Upstash: prod Redis.
- All secrets in Fly.io secrets, not env files.
- Sentry release tracking wired to deploys.
- PostHog: prod project.
- App Store Connect: app submitted for review.
- Play Console: app submitted for review.

### 10. Soft launch (Day 8-14)

- Submit to App Store + Play Store.
- Day 1: 100 internal testers via TestFlight + Play internal track.
- Day 3: 1000 external testers via TestFlight.
- Day 7: open beta in Nigeria only (App Store + Play Store support country-specific soft launches).
- Day 14: full launch if metrics look good.

## What's out of scope

- ❌ Live comments.
- ❌ AI recommendations.
- ❌ Offline downloads.
- ❌ Cross-app sharing to TikTok / Reels.
- ❌ Multi-region redundancy (single Fly.io region for now).
- ❌ Web admin (mobile admin only).
- ❌ Refund automation (still manual via App Store Connect).

## Tasks (ordered, with line estimates)

1. **Sentry mobile + backend** — SDK wired, source maps, release tracking. **~ 200 lines + config.**
2. **PostHog mobile + backend** — SDK wired, events, funnels. **~ 300 lines + config.**
3. **Finance dashboard** — `services/finance.py`, materialised view, cron refresh, `finance.tsx`. **~ 600 lines.**
4. **Moderation dashboard** — auto-flag, mobile moderation screen. **~ 400 lines.**
5. **Cron jobs** — `worker/cron.py`, 4 jobs. **~ 400 lines.**
6. **Rate limiting** — `core/rate_limit.py`, applied to 4 endpoints. **~ 200 lines.**
7. **CDN caching** — Cloudflare config + cache headers in FastAPI. **~ 100 lines + config.**
8. **i18n** — 5 JSON files, `lib/i18n.ts`, all UI strings extracted. **~ 1500 lines (mostly translations).**
9. **Production deploy** — Fly.io config, secrets, deploy script. **~ 200 lines + config.**
10. **Store submission** — privacy policy, support URL, age rating, screenshots. **~ 50 lines + assets.**

Total: **~ 4,000 lines of new code + a lot of config + a lot of clicking in dashboards.**

## Verification

The "is it working in production" check:

```bash
# Health check
curl -fsS https://api.vidashort.app/health
# → {"db":"ok","redis":"ok","sentry":"ok"}

# Sentry: no errors in the dashboard for 24h after launch.
# PostHog: dashboard shows the expected funnels populating.

# From a real device:
# - Sign up. Sign in. Sentry sees no errors.
# - Watch 3 episodes. PostHog sees 3 'episode_complete' events.
# - Hit a paywall. PostHog sees 'paywall_open'.
# - Pay 25 coins. PostHog sees 'paywall_convert'.
```

**Pass criteria (for the 2-week soft launch):**
- 99.5% uptime on the API.
- < 1% crash rate on the mobile app.
- < 5% 5xx on the API.
- Daily active users > 1,000 by day 14.
- Paying users > 1% of DAU.
- ARPU > ₦50/day.
- No Sentry errors above `warning` in the happy path.
- App Store rating > 4.0 after 50 reviews.
- Play Store rating > 4.0 after 50 reviews.

If any of these are off, **don't launch wider.** Fix first, then re-launch.

## Hand-off

What Phase 6 (beyond) assumes:
- The app is in production, with real users, real money, real data.
- The Sentry + PostHog dashboards are monitored daily.
- The finance dashboard shows the platform is profitable.
- The admin team can moderate and pay out without engineering help.
- The mobile + backend are stable enough that adding new features is low-risk.

What this phase's runbook is:
- `docs/runbooks/incident-response.md` (new, Phase 5)
- `docs/runbooks/deploy.md` (new, Phase 5)
- `docs/runbooks/rollback.md` (new, Phase 5)
