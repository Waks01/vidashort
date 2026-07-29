"""Health check tests — /health must ping DB + Redis (CLAUDE.md §11 / Phase 2 §7)."""
import pytest


@pytest.mark.asyncio
async def test_health_returns_200_with_ok_subsystems(client, fake_redis):
    """Happy path: both DB and Redis up → 200 + {ok: true, db: ok, redis: ok}."""
    resp = await client.get("/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["db"] == "ok"
    assert body["redis"] == "ok"


@pytest.mark.asyncio
async def test_health_returns_503_when_redis_down(client, fake_redis):
    """If Redis can't be reached, /health must surface that as 503 with
    `redis: down` so the on-call knows exactly which subsystem failed."""
    fake_redis.up = False
    resp = await client.get("/health")
    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert body["ok"] is False
    assert body["db"] == "ok"
    assert body["redis"] == "down"