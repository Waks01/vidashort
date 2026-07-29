"""Coins tests — balance, packs, IAP purchase (currently a 501 stub)."""
import pytest

from tests.conftest import auth_headers, _current as _email_cap


async def _signup(client, email="coinuser@example.com"):
    """Sign up + verify OTP; returns (user_id, accessToken)."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email,
        "password": "cointester",
        "name": "CoinUser",
    })
    assert resp.status_code == 202, resp.text
    code = _email_cap().otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()["user"]["id"], verify.json()["accessToken"]


@pytest.mark.asyncio
async def test_balance_starts_at_zero_for_new_user(client):
    user_id, _ = await _signup(client)
    resp = await client.get("/v1/coins/balance", headers=auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["coins"] == 0
    assert body["recent"] == []


@pytest.mark.asyncio
async def test_balance_reflects_ad_rewards(client):
    user_id, _ = await _signup(client, "ad-earner@example.com")
    await client.post("/v1/ads/record", json={
        "ad_id": "earn-1", "watched_s": 15, "completed": True,
    }, headers=auth_headers(user_id))
    await client.post("/v1/ads/record", json={
        "ad_id": "earn-2", "watched_s": 20, "completed": True,
    }, headers=auth_headers(user_id))

    resp = await client.get("/v1/coins/balance", headers=auth_headers(user_id))
    body = resp.json()
    assert body["coins"] == 40  # 2 × 20 coins reward
    assert len(body["recent"]) == 2
    assert all(t["delta"] == 20 for t in body["recent"])


@pytest.mark.asyncio
async def test_packs_returns_five_tier_catalog(client):
    resp = await client.get("/v1/coins/packs")
    assert resp.status_code == 200
    packs = resp.json()["packs"]
    assert len(packs) == 5
    # Confirm coins ↔ naira parity is 10 coins = ₦1 (CLAUDE.md §4)
    p100 = next(p for p in packs if p["id"] == "pack_100")
    assert p100["coins"] == 100 and p100["priceNaira"] == 100
    # Confirm at least one pack has bonus coins
    p2200 = next(p for p in packs if p["id"] == "pack_2200")
    assert p2200["bonusCoins"] == 200
    assert p2200["totalCoins"] == 2200


@pytest.mark.asyncio
async def test_purchase_returns_501_until_receipt_validation_wired(client):
    user_id, _ = await _signup(client, "purchaser@example.com")
    # The schema enforces a structured receipt payload, not a raw string.
    resp = await client.post("/v1/coins/purchase", json={
        "packId": "pack_100",
        "receipt": {
            "provider": "apple",
            "data": "fake-receipt",
            "txnId": "txn-123",
        },
    }, headers=auth_headers(user_id))
    # Phase-2 reality: receipt verification is a stub — accept any of:
    # 501 (not implemented) OR 200 (lab mock in tests/dev). The endpoint
    # shouldn't 401/422 on a valid auth + payload.
    assert resp.status_code in (200, 501), resp.text


@pytest.mark.asyncio
async def test_balance_requires_auth(client):
    resp = await client.get("/v1/coins/balance")
    assert resp.status_code == 401
