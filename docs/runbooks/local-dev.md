# Runbook — local dev setup

Phase 1 (mobile) and Phase 2 (backend) have specific local setup needs. This runbook covers the first-time setup.

## Prerequisites

- **Node 22.x** (`nvm install 22 && nvm use 22`).
- **Python 3.12** (`pyenv install 3.12 && pyenv local 3.12` or just `python3.12`).
- **uv** for Python deps (`pip install uv` or `brew install uv`).
- **Docker Desktop** for Postgres + Redis (Phase 2+).
- **iOS Simulator** (Xcode) for iOS testing.
- **Android Studio** + an emulator for Android testing.
- **Expo Go** app on a real device for quick smoke tests.

## Phase 1 — mobile only

```bash
# From repo root
nvm use 22  # or your preferred node version manager
npm install  # installs workspaces

# OneDrive exclusion (one-time per machine)
# See docs/runbooks/onedrive-exclude.md

# Start mobile
npm run mobile
# This is `npm --workspace apps/mobile run start`
# → opens Expo dev tools in browser
# → choose iOS simulator or Android emulator
```

The first `npm install` is slow (~ 5 min) because `node_modules/` is huge. Subsequent installs are fast.

## Phase 2 — backend (adds the API)

```bash
# One-time: install Python 3.12 + uv
pyenv install 3.12
pyenv local 3.12
pip install uv

# Start Postgres + Redis locally
cd apps/api
docker-compose up -d

# Install Python deps
uv sync

# Run migrations
uv run alembic upgrade head

# Seed local data (Phase 2: empty; Phase 2.5: TMDB seed)
# uv run python scripts/seed.py

# Start the API
uv run uvicorn app.main:app --reload
# → http://localhost:8000

# Verify
curl http://localhost:8000/health
# → {"status":"ok","db":"ok","redis":"ok"}
```

## Phase 2+ — mobile points at local API

```bash
# In apps/mobile/.env (gitignored)
echo "EXPO_PUBLIC_ENV=dev" > apps/mobile/.env
echo "EXPO_PUBLIC_API_URL=http://localhost:8000/v1" >> apps/mobile/.env

# In another terminal
npm run mobile
# On iOS Simulator, the app will hit localhost:8000. The simulator can reach localhost.
# On Android Emulator, the host is 10.0.2.2 (Android-specific). Update the .env.
```

## What to do if `npm install` fails

- Clear `node_modules/` and `package-lock.json` in the workspace, retry.
- Clear npm cache: `npm cache clean --force`.
- If a specific package fails, check the Expo SDK 57 version compatibility matrix.
- If still stuck: read `mobile/AGENTS.md` (we have a strict version policy).

## What to do if `docker-compose up` fails

- Docker Desktop not running → start it.
- Port 5432 already in use → `lsof -i :5432` (Mac/Linux) or `netstat -ano | findstr :5432` (Windows). Stop the conflicting service, or change the port in `docker-compose.yml`.
- Memory limit → bump Docker Desktop's memory allocation to 4 GB+.

## What to do if `uvicorn` fails to start

- Postgres not running → `docker-compose ps`, then `docker-compose up -d`.
- Redis not running → same.
- Migration not run → `uv run alembic upgrade head`.
- Pydantic complains about env vars → check `.env` exists, has all the required keys.

## Editor setup (recommended)

- **VS Code:**
  - Extensions: ESLint, Prettier, Python, Pylance, Tailwind IntelliSense (for the prototype), Expo Tools, React Native Tools.
  - Workspace settings: format on save, type-check on save.
- **Cursor / Windsurf:** fine, same extensions apply.
- **PyCharm:** also fine. Set the project interpreter to `.venv/bin/python` (or the `uv` venv).

## Where things live

- `apps/mobile/` — Expo app. Edit here for mobile work.
- `apps/api/` — FastAPI. Edit here for backend work.
- `apps/design/` — visual prototype. Read-only from Phase 1 onwards.
- `docs/` — the docs you're reading. Edit here for spec changes.
- `packages/shared/` — zod schemas. Used by both mobile and (eventually) backend tests.

## Daily workflow

Most days, you only need:

```bash
# Terminal 1: backend
cd apps/api
docker-compose up -d  # if not already running
uv run uvicorn app.main:app --reload

# Terminal 2: mobile
npm run mobile

# Then in your editor: edit code, save, the relevant process hot-reloads.
```

That's it. Read `docs/steering/00-rules.md` before making changes.
