# vidashort-api

FastAPI backend for vidashort.

## Setup

```bash
cp .env.example .env
# edit .env with your values
```

## Run locally (three services via compose)

```bash
# One command — postgres, redis, and the api all come up:
./scripts/up.sh

# When you're done:
./scripts/down.sh            # keeps data
./scripts/down.sh --wipe     # wipes data (fresh DB next time)
```

`scripts/up.sh` runs `docker compose up -d`, waits for `/health` to return 200, then runs `alembic upgrade head` (idempotent). The api is on `http://localhost:8000`.

## Run migrations manually

```bash
docker compose exec api alembic upgrade head
```