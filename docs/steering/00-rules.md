# Steering — what to do, what not to do, how to make decisions

This is the operating manual. **Any agent touching this repo must read this file.** It is enforced by the project; it is not optional.

## The 12 rules

### Rule 1 — Source of truth hierarchy

If two documents disagree, the order of authority is:

1. **The user.** Always. If the user says X, do X.
2. **This file** (`docs/steering/00-rules.md`) + `CLAUDE.md`.
3. **`docs/brand/`** — brand identity. Visual decisions.
4. **`docs/contracts/`** — frontend ↔ backend wire format.
5. **`docs/api/`** — endpoint specs.
6. **`docs/architecture/`** — system shape.
7. **`docs/backend/` and `docs/mobile/`** — component trees.
8. **`docs/phases/`** — implementation specs for the current phase.
9. **The plan file** (`C:\Users\kenik\.claude\plans\harmonic-watching-knuth.md`) — session log of decisions, may be out of date.
10. **The code itself** — reflects the most recent work but may lag.

When you find a contradiction, **stop and ask the user**. Do not pick the one you "think is right."

### Rule 2 — Read before write

Before editing any file, read it in full. Before writing any new file, read the 3 nearest neighbors (the directory it's going in, the README of that directory if any, and a sibling file).

Before asking the user "should I do X?", check whether the answer is already in the docs. Most of the time it is.

### Rule 3 — Visual prototype is the brand source of truth

For look-and-feel, `apps/design/` wins. The mobile and backend specs describe **behavior and shape**, not pixels. If a design choice in the prototype contradicts a token in `docs/brand/`, the token wins (and the prototype should be updated to match). If a design choice in the prototype contradicts an API contract, the contract wins (and the prototype's mocked data is wrong).

### Rule 4 — Locked numbers are sacred

The economics in `CLAUDE.md § 4` cannot be changed without explicit user approval. They are the product. If a task says "set the rewarded ad to 30 coins" — refuse, point at the locked value, ask the user.

### Rule 5 — localStorage schema is public API

`apps/design/scripts/app.js` defines keys like `vidashort.user.coins`, `vidashort.user.dailyStreak`, etc. These are mirrored to the backend's Postgres schema in Phase 2. **Do not rename a key without a migration plan.** If you must change a key, add a one-shot migration in the bootstrap that reads the old key and writes the new one.

The full schema is in `apps/design/scripts/data.js` (the MockData user object) and `app.js` (Storage). Treat them as the canonical names until the backend takes over.

### Rule 6 — Don't add dependencies without asking

The mobile app will get a `package.json`. The backend will get a `pyproject.toml`. **Both start minimal.** Before adding a dependency:

1. Check if the standard library covers it (Python: `pathlib`, `dataclasses`, `enum`, `secrets`. JS: native fetch, AbortController, URL, Intl).
2. Check if an existing dependency covers it.
3. If you must add, **state the package, the version, and the reason** to the user. Get approval.

Forbidden dependencies (without explicit user override):
- ❌ `lodash` / `underscore` (use modern JS).
- ❌ `moment` (use `date-fns` or `Intl`).
- ❌ `axios` (use `fetch`).
- ❌ `redux` / `mobx` (use React context + URL state).
- ❌ `styled-components` / `emotion` (use `StyleSheet.create` + the token module).
- ❌ `tailwindcss` (use the token system).
- ❌ `react-native-paper` / `native-base` (we own our components).
- ❌ `faker` (hand-write the seed data; it has a voice).
- ❌ `prisma` (we use SQLAlchemy 2).
- ❌ `pydantic v1` (we use v2).

### Rule 7 — Don't fight the platform

- **React Native** is not the web. If something feels awkward, it's because RN isn't a browser. Don't bring in web-only libraries (`react-router`, `react-helmet`).
- **FastAPI** is not Django. Don't add Django-style signals, middleware everywhere, or app configs.
- **Postgres** is not MongoDB. If you find yourself wanting to store a JSON blob in a column, you probably want a join.
- **Cloudflare Stream** returns signed URLs that expire. Don't try to cache them longer than 1 hour.

### Rule 8 — Money is integers

- All coin amounts in the API are **integers**. No floats. No decimals. No "12.5 coins."
- Naira values are floats for display only, **never** in storage or API.
- Coin → Naira conversion: `coins / 10 = naira` (locked).
- Naira → Coin: `Math.floor(naira * 10)`. Round **down**. The platform absorbs the fractional.

### Rule 9 — Every API endpoint is versioned

All routes are under `/v1/`. When you add a breaking change, it's `/v2/`. The v1 contract is documented in `docs/api/` and never changes after launch.

Non-breaking additions (new fields, new endpoints, new optional query params) are fine in v1.

### Rule 10 — Every screen has a back

- Every modal has a close X (visible at all times, even on a paywall).
- Every sheet has a drag handle + an X.
- Every sub-screen has a back button in the top bar.
- Every sub-screen has an escape hatch (back gesture on iOS, hardware back on Android, browser back on web).
- The paywall's close X must lead somewhere — if user can't pay, the X returns them to the previous screen (or home, never to a blank state).

### Rule 11 — Never log secrets

No JWT tokens, no refresh tokens, no IAP receipts, no ad SDK keys in plaintext logs. If a tool needs to log a request, log the method + path + status code, not headers or bodies.

Sentry / PostHog / Mixpanel keys are public-ish but still go in `expo.extra` / `.env`, never in code committed to git.

### Rule 12 — One thing at a time, fully done

When a phase is in progress, **finish it before starting the next.** "Phase 1 verification: signup → /v1/me works end-to-end" is a binary gate, not a milestone. If Phase 1 verification is failing, Phase 2 does not start.

"No half-done work" means:
- Every screen renders without console errors.
- Every CTA leads somewhere real.
- Every form validates.
- Every error state is reachable.
- Every state is tested (manually is fine for the prototype; automated once we're past Phase 0.5).

## What to do

### When you start a session
1. Read `CLAUDE.md` (you've done this).
2. Skim `docs/phases/00-roadmap.md` to know which phase is active.
3. Read the **active phase spec** end to end.
4. Read the **relevant component tree** (`docs/mobile/00-tree.md` if mobile, `docs/backend/00-tree.md` if API).
5. Skim the **brand tokens** (`docs/brand/20-tokens.md`) for any visual work.

### When you make a change
1. Read the file you're about to edit, in full.
2. Make the change.
3. **Verify the change.** For prototype: open the affected screen. For backend: hit the endpoint with curl. For mobile: build and run on simulator.
4. If the change is visible to the user, **show them before moving on.**

### When you discover a bug
1. Reproduce it. Get the exact steps and the exact output.
2. Check if the bug is already in the docs as a known issue.
3. If it's new, fix it. If the fix is risky (>20 lines, touches locked code, changes a contract), stop and ask.
4. After the fix, **add a regression test or a smoke check** so it doesn't come back.

### When you finish a phase
1. Run the **verification section** of the phase spec end to end.
2. Update `docs/phases/00-roadmap.md` to mark the phase complete and set the next one to in-progress.
3. **Commit the docs change with the code change.** The roadmap is the source of truth, not the plan file.
4. Tell the user "Phase X is done. Ready for Phase X+1." Then stop.

## What NOT to do

- ❌ Don't commit secrets. Ever. `.env` files go in `.gitignore`.
- ❌ Don't push to a remote without the user saying "push it."
- ❌ Don't merge a PR you didn't open (the user opens them).
- ❌ Don't start a phase that's gated by an unverified earlier phase.
- ❌ Don't refactor something that "looks wrong" without checking the spec first. The code may match the spec, and the spec may be right.
- ❌ Don't add a `TODO:` without a tracking issue / phase reference.
- ❌ Don't disable a type check, lint rule, or test "temporarily." The temporary is forever.
- ❌ Don't use `as any` in TypeScript. If you need it, the type is wrong; fix the type.
- ❌ Don't use `except Exception: pass` in Python. Catch the specific exception.
- ❌ Don't say "done" without verification. "Done" means the verification section of the spec passed.
- ❌ Don't say "should work" or "should be fine." Verify, then say "works" with evidence.
- ❌ Don't introduce a new design pattern without writing it down. The docs are part of the code.

## Decision tree when blocked

```
Am I blocked on a USER decision?
  → AskUserQuestion. Wait for answer.
  → Do NOT pick a default and proceed.

Am I blocked on a FACT in the code?
  → Read the relevant file. If unclear, read 3 sibling files.
  → Still unclear? Run the code and observe.
  → Still unclear? Ask the user.

Am I blocked on a FACT in an external system (Expo, FastAPI, etc.)?
  → WebSearch / WebFetch the versioned docs.
  → Permissions allow WebSearch freely. WebFetch is restricted to apkpure.com and play.google.com.
  → For other domains, ask the user to add the domain or to use WebSearch instead.

Am I blocked on a CHOICE between two equally valid approaches?
  → Pick the one with the smallest blast radius.
  → Note the choice in the plan file and the relevant doc.
  → If the user disagrees later, undoing is easy because the blast radius was small.
```

## When the user disagrees with this file

The user is the highest authority. If they say "actually, do X" where X contradicts this file, do X, and then **propose an edit to this file** in your next message.

The docs evolve. The user evolves the docs.

## Summary

> Read. Verify. Don't lie. Don't half-do. Don't break the locked numbers. Don't add dependencies. Don't fight the platform. Don't log secrets. Ask when blocked. Update the docs when you learn something.

That's the whole job.
