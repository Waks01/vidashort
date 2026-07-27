# docs/ — the vidashort spec tree

This is the durable spec for the project. Any agent (human or AI) who joins mid-stream should start here. The plan file (`C:\Users\kenik\.claude\plans\harmonic-watching-knuth.md`) is the **session log** of decisions; this `docs/` tree is the **canonical spec** that survives across sessions.

## How to read this tree

```
docs/
├── brand/          ← design system: colors, type, tokens, style guide
├── architecture/   ← system shape, monorepo layout, the three apps
├── api/            ← every endpoint, request/response, errors
├── contracts/      ← frontend ↔ backend wire format
├── backend/        ← FastAPI tree + Postgres schema
├── mobile/         ← Expo tree + component layering
├── phases/         ← roadmap + per-phase implementation specs
├── steering/       ← rules, what to do, what NOT to do
└── runbooks/       ← local-dev, onedrive, debugging, onboarding
```

**Start at `CLAUDE.md` at the repo root.** It tells you what to read in what order.

## Every file in this tree, by purpose

### Entry point

| File | Purpose |
|---|---|
| `../CLAUDE.md` | Project entry point. Read first. |
| `../README.md` | Human-facing readme. |

### Brand (`docs/brand/`)

| File | What it covers |
|---|---|
| `00-overview.md` | Brand identity, voice, color tokens, type, motion, accessibility, "what never to do" |
| `10-typography.md` | Font loading, type roles, scale, weights, common mistakes |
| `20-tokens.md` | The complete token system (colors, spacing, radius, motion, z-index) — machine-readable reference for both CSS and TS |
| `30-style-guide.md` | Component patterns, layout patterns, do/don't by component |

### Architecture (`docs/architecture/`)

| File | What it covers |
|---|---|
| `00-overview.md` | System diagram, the three apps, how they talk, repository layout |
| `10-monorepo.md` | npm workspaces layout, .gitignore, package.json shapes per app, OneDrive reality |

### API (`docs/api/`)

| File | What it covers |
|---|---|
| `00-overview.md` | Base URL, auth, versioning, pagination, error envelope, status codes, rate limits, idempotency, CORS, route map |
| `01-auth.md` | signup, signin, refresh, apple, google, forgot, reset, JWT shape, security |
| `02-me.md` | GET/PATCH /v1/me, age-confirm, delete, user shape |
| `03-content.md` | Series list/detail, stream URL, featured, favorites, shapes |
| `04-entitlement.md` | The paywall decision tree, check, unlock, creator credit math, watch history |
| `05-coins.md` | Balance, packs, purchase (IAP), refund, IAP libs |
| `06-ads.md` | Cap, record, rewarded + interstitial, anti-cheat |
| `07-creator.md` | Profile, series CRUD, upload URLs, analytics, earnings, payouts |
| `08-admin.md` | Overview, moderation, content, users, ads, finance, audit log |
| `09-webhooks.md` | Cloudflare, RevenueCat, Apple, Google, signature verification |

### Contracts (`docs/contracts/`)

| File | What it covers |
|---|---|
| `00-overview.md` | Auth flow, error handling, idempotency, caching, paywall flow, video, IAP, push, offline, env, logging, request shape |

### Backend (`docs/backend/`)

| File | What it covers |
|---|---|
| `00-tree.md` | FastAPI tree, layering rules, hot tables, the paywall service code, auth, config, why SQLAlchemy 2 + Pydantic v2 |
| `10-schema.md` | All 14 tables, DDL, indexes, migration policy |

### Mobile (`docs/mobile/`)

| File | What it covers |
|---|---|
| `00-tree.md` | Expo tree, layering, the hooks pattern, the api client, state management, storage, navigation, why no styled-components / nativewind / paper |

### Phases (`docs/phases/`)

| File | What it covers |
|---|---|
| `00-roadmap.md` | All phases, locked economics, locked product rules, critical-path rules |
| `01-mobile-skeleton.md` | Phase 1 — Expo app boots, design system in TS, mock API, (auth) + (viewer) shells |
| `02-backend-skeleton.md` | Phase 2 — FastAPI + Neon + Upstash, auth + me, mobile flips to real |
| `03-monetization.md` | Phase 3 — paywall, coins, ads, creator, admin, player |
| `04-polish.md` | Phase 4 — comments, share, library, settings, push, search, discover, state screens |
| `05-observability.md` | Phase 5 — Sentry, PostHog, finance dashboard, cron, rate limit, CDN, i18n, prod deploy, soft launch |

### Steering (`docs/steering/`)

| File | What it covers |
|---|---|
| `00-rules.md` | The 12 hard rules, what to do, what NOT to do, decision tree when blocked |

### Runbooks (`docs/runbooks/`)

| File | What it covers |
|---|---|
| `agent-onboarding.md` | First-time setup for a new agent: read order, environment, "do not" short list |
| `local-dev.md` | Local dev for mobile + backend, prerequisites, common failure modes |
| `onedrive-exclude.md` | OneDrive exclusion (Windows UI, no CLI available) |
| `debugging.md` | How to find a bug, common patterns in this codebase |

## How this tree evolves

When a phase completes:
- The phase spec moves from "in progress" to "done" in `00-roadmap.md`.
- The next phase's spec is updated to reflect what was learned.
- A runbook is added if a new operational pattern emerges (e.g. `incident-response.md` in Phase 5).

When a contract changes (a new endpoint, a new error code, a new field):
- The change goes in `docs/api/0X-*.md` first.
- The mobile + backend trees in `docs/mobile/00-tree.md` and `docs/backend/00-tree.md` are updated to reference the new shape.
- The contract in `docs/contracts/00-overview.md` is updated if it's a wire-level change.

When a brand decision changes (a new color, a new type role, a new component):
- `docs/brand/00-overview.md` is updated first.
- The token system in `docs/brand/20-tokens.md` is updated.
- The visual prototype (`apps/design/styles/tokens.css`) is updated to match.
- The mobile token module (`apps/mobile/src/lib/theme/tokens.ts`, Phase 1+) is updated to match.

When a rule changes (a new "do not" or a new "always"):
- `docs/steering/00-rules.md` is updated.
- The relevant phase spec is updated if it relies on the rule.
- The plan file is **not** updated (the plan is the log, not the spec).

## How this tree is **not** updated

- ❌ Don't add changelogs. Git is the changelog.
- ❌ Don't duplicate content across files. If something is true, it lives in one place and is referenced.
- ❌ Don't move from spec to "summary" — the spec is the spec, the summary is a runbook.
- ❌ Don't write specs for things we're not building. (The Phase 6+ tree is intentionally absent.)
- ❌ Don't add screenshots. They're in the design prototype, not the docs.

## What if a file in the docs is wrong?

1. The doc is **always** more right than the code, until the code proves otherwise. Code can have bugs; docs shouldn't (and if they do, they get fixed).
2. If you find a contradiction between the doc and the code:
   - Is the code doing what the doc says? → the doc is right, the code is wrong. Fix the code.
   - Is the doc out of date? → fix the doc to match the code, **and** leave a note: "Updated YYYY-MM-DD: code did X, doc was Y. Reason: Z."
   - Are you sure which is right? → ask the user.
3. If you find a contradiction between two docs:
   - Brand wins over contracts.
   - Contracts win over API.
   - API wins over backend/mobile trees.
   - Trees win over phases.
   - If still unclear → ask the user.

---

**You finished reading this. Next: `docs/phases/00-roadmap.md` to see where we are, then the active phase spec.**
