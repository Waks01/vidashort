# vidashort-api

FastAPI backend for vidashort.

## Setup

```bash
cp .env.example .env
# edit .env with your values
```

## Run locally

```bash
docker compose up --build
```

## Run migrations

```bash
docker compose exec api alembic upgrade head
```