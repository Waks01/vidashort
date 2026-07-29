#!/usr/bin/env bash
# scripts/up.sh
# One-command bring-up for local development.
# Runs `docker compose up -d`, waits for the api's /health to return 200,
# then runs alembic upgrade head (idempotent). Idempotent: safe to re-run.

set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> docker compose up -d"
docker compose up -d

# Wait for the api's healthcheck to flip to healthy (max 60s).
echo "==> Waiting for http://localhost:8000/health ..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "==> API is healthy"
    break
  fi
  sleep 1
done

if ! curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  echo "==> API failed to become healthy in 60s. Tail of api logs:"
  docker compose logs --tail=40 api
  exit 1
fi

# Apply any pending migrations. No-op once at head.
echo "==> alembic upgrade head"
docker compose exec -T api alembic upgrade head

echo
echo "==> API on http://localhost:8000  (docs at /docs)"
echo "==> Inspect:  docker compose ps"
echo "==> Logs:     docker compose logs -f api"
echo "==> Stop:     ./scripts/down.sh            # keep data"
echo "==> Wipe:     ./scripts/down.sh --wipe     # delete data too"