"""Webhook tests — signature verification + handler behavior."""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import insert

from app.core.config import settings
from app.db.models import Episode, Series, User, VipEntitlement
from tests.conftest import auth_headers


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ---------------- Cloudflare Stream ----------------

@pytest.mark.asyncio
async def test_cloudflare_webhook_rejects_bad_signature(client):
    body = json.dumps({"uid": "abc"}).encode()
    resp = await client.post(
        "/v1/webhooks/cloudflare",
        content=body,
        headers={"X-Vidashort-Signature": "wrong-signature"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cloudflare_webhook_marks_episode_ready(client, db_session):
    # Create a series + episode whose video_uid matches the webhook payload
    series = Series(
        id=str(uuid.uuid4()), slug="cf-test", title="CF",
        synopsis="", cover_url="", category="drama", language="en",
        source="original", creator_id=None, is_published=True,
        free_episodes=3, total_episodes=5,
    )
    db_session.add(series)
    await db_session.flush()
    ep = Episode(
        id=str(uuid.uuid4()),
        series_id=series.id,
        number=1, title="Ep1", synopsis="", duration_s=120,
        video_uid="cloudflare-uid-XYZ",
        video_ready=False,
        required_coins=25,
        is_free=False,
    )
    db_session.add(ep)
    await db_session.commit()

    payload = {"uid": "cloudflare-uid-XYZ"}
    body = json.dumps(payload).encode()
    sig = _sign(settings.cf_stream_signing_key, body)

    resp = await client.post(
        "/v1/webhooks/cloudflare",
        content=body,
        headers={"X-Vidashort-Signature": sig},
    )
    assert resp.status_code == 202
    assert resp.json() == {"ok": True}

    # Verify the episode got flipped
    from sqlalchemy import select as _select
    refreshed = (await db_session.execute(
        _select(Episode).where(Episode.id == ep.id).execution_options(populate_existing=True)
    )).scalar_one()
    assert refreshed.video_ready is True


# ---------------- RevenueCat (VIP) ----------------

@pytest.mark.asyncio
async def test_revenuecat_initial_purchase_activates_vip(client, db_session):
    user_id = uuid.uuid4().__str__()
    user = User(
        id=user_id,
        email="vip-rev@example.com",
        name="VipRev",
        role="viewer",
        coins=0,
    )
    db_session.add(user)
    await db_session.commit()

    payload = {
        "event": {
            "type": "INITIAL_PURCHASE",
            "app_user_id": user_id,
        },
    }
    body = json.dumps(payload).encode()
    sig = _sign(settings.revenuecat_webhook_secret, body)

    # The handler calls fetch_subscriber_info() — patch it (async) so the test
    # doesn't hit the real RevenueCat API.
    from app.integrations import revenuecat as rc_int
    original_fetch = rc_int.fetch_subscriber_info
    async def fake_fetch(_uid):
        return {
            "entitlements": {
                "vip": {
                    "product_identifier": "vip_monthly",
                    "expires_date_ms": int((datetime.utcnow() + timedelta(days=30)).timestamp() * 1000),
                },
            },
        }
    rc_int.fetch_subscriber_info = fake_fetch
    try:
        resp = await client.post(
            "/v1/webhooks/revenuecat",
            content=body,
            headers={"X-Vidashort-Signature": sig},
        )
    finally:
        rc_int.fetch_subscriber_info = original_fetch

    assert resp.status_code == 202, resp.text

    from sqlalchemy import select as _select
    vip = (await db_session.execute(
        _select(VipEntitlement).where(VipEntitlement.user_id == user_id)
    )).scalar_one_or_none()
    assert vip is not None
    assert vip.source == "revenuecat"
    assert vip.product_id == "vip_monthly"
    assert vip.expires_at > datetime.utcnow()


@pytest.mark.asyncio
async def test_revenuecat_rejects_bad_signature(client):
    body = b'{"event":{"type":"INITIAL_PURCHASE","app_user_id":"x"}}'
    resp = await client.post(
        "/v1/webhooks/revenuecat",
        content=body,
        headers={"X-Vidashort-Signature": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_revenuecat_404s_for_unknown_app_user_id(client):
    payload = {"event": {"type": "INITIAL_PURCHASE", "app_user_id": "ghost-user"}}
    body = json.dumps(payload).encode()
    sig = _sign(settings.revenuecat_webhook_secret, body)

    resp = await client.post(
        "/v1/webhooks/revenuecat",
        content=body,
        headers={"X-Vidashort-Signature": sig},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "user_not_found"


# ---------------- Signature helper (unit-level) ----------------

def test_verify_signature_is_constant_time():
    from app.services.webhooks import verify_signature
    secret = "topsecret"
    body = b'{"hello":"world"}'
    good = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, good) is True
    assert verify_signature(secret, body, "0" * 64) is False
    assert verify_signature("", body, good) is False  # no secret → reject
    assert verify_signature(secret, body, "") is False  # no header → reject