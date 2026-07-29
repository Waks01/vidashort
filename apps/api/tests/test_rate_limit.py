"""Sign-in rate-limit tests — 5 attempts / 10 min / email (Phase 2 §4)."""
import pytest

from tests.conftest import signup_and_verify


@pytest.mark.asyncio
async def test_signin_rate_limit_blocks_after_5_attempts(client, fake_redis):
    """After 5 wrong passwords for the same email, the 6th attempt returns
    429 rate_limited regardless of whether the password is now correct."""
    body = await signup_and_verify(
        client, email="rl-alice@example.com", password="rightpw12345", name="Alice"
    )
    # Now intentionally fail sign-in 5 times.
    for i in range(5):
        resp = await client.post("/v1/auth/signin", json={
            "email": "rl-alice@example.com", "password": "wrong",
        })
        assert resp.status_code == 400, f"attempt {i + 1}: {resp.text}"

    # 6th — even with the correct password — must 429.
    blocked = await client.post("/v1/auth/signin", json={
        "email": "rl-alice@example.com", "password": "rightpw12345",
    })
    assert blocked.status_code == 429, blocked.text
    assert blocked.json()["error"] == "rate_limited"

    # The token from signup is still valid (rate-limit doesn't kill sessions).
    me = await client.get("/v1/me", headers={"Authorization": f"Bearer {body['accessToken']}"})
    assert me.status_code == 200, me.text


@pytest.mark.asyncio
async def test_signin_rate_limit_resets_on_success(client, fake_redis):
    """A successful sign-in wipes the counter so the user isn't punished for
    fat-fingering their password a few times."""
    await signup_and_verify(
        client, email="rl-bob@example.com", password="rightpw12345", name="Bob"
    )

    # 3 wrong attempts — still below the threshold.
    for _ in range(3):
        resp = await client.post("/v1/auth/signin", json={
            "email": "rl-bob@example.com", "password": "wrong",
        })
        assert resp.status_code == 400

    # Successful sign-in — counter resets.
    ok = await client.post("/v1/auth/signin", json={
        "email": "rl-bob@example.com", "password": "rightpw12345",
    })
    assert ok.status_code == 200, ok.text

    # Now another 4 wrong attempts in a row should still 400, not 429 —
    # the counter was wiped on the success above.
    for _ in range(4):
        resp = await client.post("/v1/auth/signin", json={
            "email": "rl-bob@example.com", "password": "wrong",
        })
        assert resp.status_code == 400, resp.text


@pytest.mark.asyncio
async def test_signin_rate_limit_is_per_email(client, fake_redis):
    """Hitting the limit on alice@ must not affect bob@ — the limit key
    includes the email so it's per-account, not per-IP."""
    await signup_and_verify(
        client, email="rl-carol@example.com", password="rightpw12345", name="Carol"
    )
    await signup_and_verify(
        client, email="rl-dave@example.com", password="rightpw12345", name="Dave"
    )

    # Burn out Carol's bucket.
    for _ in range(5):
        await client.post("/v1/auth/signin", json={
            "email": "rl-carol@example.com", "password": "wrong",
        })
    blocked = await client.post("/v1/auth/signin", json={
        "email": "rl-carol@example.com", "password": "rightpw12345",
    })
    assert blocked.status_code == 429

    # Dave can still sign in — buckets are independent.
    ok = await client.post("/v1/auth/signin", json={
        "email": "rl-dave@example.com", "password": "rightpw12345",
    })
    assert ok.status_code == 200, ok.text