# Runbook — first-time onboarding for a new agent

You are a new agent on this project. Read this first.

## 1. The 5 things you must read (in order)

1. **`CLAUDE.md`** — the entry point. Tells you the project shape, locked numbers, and what to do / not do.
2. **`docs/steering/00-rules.md`** — the operating manual. Hard constraints.
3. **`docs/phases/00-roadmap.md`** — which phase we're in, what's next, what's done.
4. **The active phase spec** (e.g. `docs/phases/01-mobile-skeleton.md`) — the tasks for this round.
5. **The relevant component tree** (`docs/mobile/00-tree.md` for mobile, `docs/backend/00-tree.md` for API).

## 2. Then skim (in any order)

- `docs/brand/00-overview.md` — brand identity, colors, type. Read if you're doing visual work.
- `docs/architecture/00-overview.md` — how the three apps talk. Read if you're wiring things up.
- `docs/contracts/00-overview.md` — frontend ↔ backend wire format. Read if you're touching the API.
- The `docs/api/` file relevant to the endpoint you're changing.

## 3. Verify the environment

Run the local dev runbook:

```bash
# If Phase 1
npm install
npm run mobile

# If Phase 2
cd apps/api && docker-compose up -d && uv run uvicorn app.main:app --reload
```

If the environment doesn't boot, **stop and ask the user**. Don't fight it.

## 4. Make your changes

- Read every file before editing.
- Edit small, verify each change.
- Update the docs if you learn something.
- Don't refactor things that "look wrong" without checking the spec.

## 5. Before saying "done"

- Run the **verification section** of the phase spec.
- Confirm no `console.error` (mobile) or no `5xx` (backend).
- Run any tests that exist.
- Update the roadmap if you finished the phase.

## 6. If you're stuck

1. Re-read `docs/steering/00-rules.md` § "Decision tree when blocked."
2. Search the docs for the topic.
3. Read 2-3 files near the code you're changing.
4. If still stuck, ask the user. Do not invent.

## 7. The "do not" list (short form)

- ❌ Change locked numbers (10c/₦1, 25/episode, 20/ad, 100/day cap, 60/40 split, ₦5,000 min).
- ❌ Add dependencies without asking.
- ❌ Skip the verification step.
- ❌ Commit secrets, tokens, or `.env` files.
- ❌ Push to a remote without the user saying "push it."
- ❌ Start a phase before the previous one is verified.
- ❌ Refactor without a reason in the docs.
- ❌ Use emoji as icons.
- ❌ Use Comic Sans. (Yes, again.)

## 8. Quick reference

- **Locked numbers:** `CLAUDE.md` § 4
- **Stack:** `CLAUDE.md` § 5
- **Brand:** `docs/brand/00-overview.md`
- **System shape:** `docs/architecture/00-overview.md`
- **API:** `docs/api/00-overview.md` + per-domain files
- **Mobile tree:** `docs/mobile/00-tree.md`
- **Backend tree:** `docs/backend/00-tree.md`
- **Frontend ↔ backend contract:** `docs/contracts/00-overview.md`
- **Roadmap:** `docs/phases/00-roadmap.md`
- **Active phase:** `<the latest 0X-*.md>` in `docs/phases/`
- **Local dev:** `docs/runbooks/local-dev.md`
- **OneDrive:** `docs/runbooks/onedrive-exclude.md`

Welcome. Read carefully. Verify everything. Update the docs.
