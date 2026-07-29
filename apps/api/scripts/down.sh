#!/usr/bin/env bash
# scripts/down.sh
# Stop the dev stack. Pass --wipe to also delete the postgres + redis
# volumes (fresh DB on next `./scripts/up.sh`). Default keeps data.

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--wipe" ]]; then
  echo "==> docker compose down -v  (this deletes the DB)"
  docker compose down -v
  echo "==> Done. Next ./scripts/up.sh starts with a fresh database."
else
  echo "==> docker compose down  (data is kept in volumes)"
  docker compose down
  echo "==> Done. Next ./scripts/up.sh resumes with the same database."
fi