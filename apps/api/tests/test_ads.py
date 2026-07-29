"""Ad cap tests — the 100/day limit is locked (CLAUDE.md §4)."""
import pytest

from tests.conftest import auth_headers, _current as _email_cap


async def _signup(client, email: str = "viewer@example.com"):
    """Sign up + verify OTP; returns (user_id, accessToken)."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email,
        "password": "adstester",
        "name": "Viewer",
    })
    assert resp.status_code == 202, resp.text
    code = _email_cap().otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()["user"]["id"], verify.json()["accessToken"]


@pytest.mark.asyncio
async def test_ad_cap_starts_at_100(client):
    user_id, token = await _signup(client)
    cap = await client.get("/v1/ads/cap", headers=auth_headers(user_id))
    assert cap.status_code == 200
    payload = cap.json()
    assert payload["limit"] == 100
    assert payload["remaining"] == 100
    assert payload["used"] == 0


@pytest.mark.asyncio
async def test_ad_record_credits_reward_coins_and_decrements_cap(client):
    user_id, token = await _signup(client, "earn@example.com")
    record = await client.post("/v1/ads/record", json={
        "ad_id": "ad-1",
        "watched_s": 15,
        "completed": True,
    }, headers=auth_headers(user_id))
    assert record.status_code == 200, record.text
    body = record.json()
    assert body["ok"] is True
    assert body["rewardedCoins"] == 20
    assert body["newBalance"] == 20
    assert body["remaining"] == 99


@pytest.mark.asyncio
async def test_ad_record_rejects_duplicate_ad_id(client):
    user_id, _ = await _signup(client, "dup@example.com")
    headers = auth_headers(user_id)
    first = await client.post("/v1/ads/record", json={"ad_id": "dup-ad", "watched_s": 10, "completed": True}, headers=headers)
    assert first.status_code == 200
    dup = await client.post("/v1/ads/record", json={"ad_id": "dup-ad", "watched_s": 10, "completed": True}, headers=headers)
    assert dup.status_code == 400
    assert dup.json()["error"] == "already_recorded"


@pytest.mark.asyncio
async def test_ad_record_rejects_watch_too_short(client):
    user_id, _ = await _signup(client, "short@example.com")
    headers = auth_headers(user_id)
    bad = await client.post("/v1/ads/record", json={"ad_id": "short-ad", "watched_s": 2, "completed": True}, headers=headers)
    assert bad.status_code == 400
    assert bad.json()["error"] == "watched_too_short"


@pytest.mark.asyncio
async def test_ad_cap_returns_429_after_100(client, db_session):
    """Insert 100 impressions directly via DB, then assert the next record 429s."""
    import uuid
    from sqlalchemy import insert

    from app.db.models import AdImpression

    user_id, _ = await _signup(client, "capbound@example.com")
    headers = auth_headers(user_id)

    # Insert 100 fake impressions via the per-test DB session (same engine the
    # client routes use, so the cap-counting query sees them).
    for i in range(100):
        await db_session.execute(insert(AdImpression).values(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ad_id=f"prefill-{i}",
            ad_network="appLovin",
            ad_type="rewarded",
            watched_s=15,
            completed=True,
            rewarded_coins=20,
        ))
    await db_session.commit()

    # The cap should now read remaining=0
    cap = await client.get("/v1/ads/cap", headers=headers)
    assert cap.json()["remaining"] == 0

    # A new ad record must 429
    blocked = await client.post("/v1/ads/record", json={"ad_id": "post-cap", "watched_s": 15, "completed": True}, headers=headers)
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "cap_reached"


@pytest.mark.asyncio
async def test_ads_record_requires_auth(client):
    resp = await client.post("/v1/ads/record", json={"ad_id": "x", "watched_s": 15, "completed": True})
    assert resp.status_code == 401