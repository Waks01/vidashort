"""Entitlement tests — paywall decision order (CLAUDE.md §4):
VIP → free → coins → ad → premium.  Each tier is tested in isolation.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import insert, select, update

from app.db.models import Series, Episode, User, VipEntitlement
from tests.conftest import auth_headers, _current as _email_cap


async def _make_series(db_session, *, slug="ent-drama", title="EntDrama",
                       free_episodes=2, total=5):
    series = Series(
        id=str(uuid.uuid4()),
        slug=slug, title=title,
        synopsis="", cover_url="", category="drama", language="en",
        source="original", creator_id=None, is_published=True,
        free_episodes=free_episodes, total_episodes=total,
    )
    db_session.add(series)
    await db_session.flush()
    for n in range(1, total + 1):
        ep = Episode(
            id=str(uuid.uuid4()),
            series_id=series.id, number=n,
            title=f"Ep {n}", synopsis="", duration_s=120,
            video_uid=f"video-{slug}-{n}", video_ready=True,
            required_coins=25, is_free=(n <= free_episodes),
        )
        db_session.add(ep)
    await db_session.commit()
    ep3 = (await db_session.execute(
        select(Episode).where(Episode.series_id == series.id, Episode.number == 3)
    )).scalar_one()
    return series, ep3


async def _signup(client, email="entuser@example.com"):
    """Sign up + verify OTP; returns (user_id, accessToken)."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email,
        "password": "entpass123!",
        "name": "Entuser",
    })
    assert resp.status_code == 202, resp.text
    code = _email_cap().otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()["user"]["id"], verify.json()["accessToken"]


@pytest.mark.asyncio
async def test_decision_free_for_episode_within_free_window(client, db_session):
    user_id, _ = await _signup(client, "free-dec@example.com")
    series, ep2 = await _make_series(db_session, slug="freewindow", free_episodes=3)

    resp = await client.post("/v1/entitlement/check", json={"episodeId": ep2.id}, headers=auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["allowed"] is True
    assert body["source"] == "free"


@pytest.mark.asyncio
async def test_decision_coins_when_user_has_enough_balance(client, db_session):
    user_id, _ = await _signup(client, "coins-rich@example.com")
    series, ep3 = await _make_series(db_session, slug="coinshavesome", free_episodes=1)
    await db_session.execute(update(User).where(User.id == user_id).values(coins=100))
    await db_session.commit()

    resp = await client.post("/v1/entitlement/check", json={"episodeId": ep3.id}, headers=auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["allowed"] is True
    assert body["source"] == "coins"


@pytest.mark.asyncio
async def test_decision_ad_when_user_has_no_coins_but_cap_remaining(client, db_session):
    user_id, _ = await _signup(client, "ad-dec@example.com")
    series, ep3 = await _make_series(db_session, slug="needsad", free_episodes=1)
    resp = await client.post("/v1/entitlement/check", json={"episodeId": ep3.id}, headers=auth_headers(user_id))
    body = resp.json()
    assert body["allowed"] is True
    assert body["source"] == "ad"
    # The paywall block carries the locked 20-coin reward
    # (paywall is passed through as a raw dict, so field names stay snake_case)
    assert body["paywall"]["reward_coins"] == 20
    assert body["paywall"]["remaining_ads"] == 100


@pytest.mark.asyncio
async def test_decision_vip_trumps_everything(client, db_session):
    user_id, _ = await _signup(client, "vip-user@example.com")
    series, ep3 = await _make_series(db_session, slug="viptests", free_episodes=1)

    # Grant an unexpired VIP entitlement
    await db_session.execute(insert(VipEntitlement).values(
        id=str(uuid.uuid4()),
        user_id=user_id,
        source="revenuecat",
        product_id="vip_monthly",
        started_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        auto_renew=True,
    ))
    await db_session.commit()

    resp = await client.post("/v1/entitlement/check", json={"episodeId": ep3.id}, headers=auth_headers(user_id))
    body = resp.json()
    assert body["allowed"] is True
    assert body["source"] == "vip"


@pytest.mark.asyncio
async def test_unlock_with_coins_debits_user(client, db_session):
    user_id, _ = await _signup(client, "unlocker@example.com")
    series, ep3 = await _make_series(db_session, slug="unlockthis", free_episodes=1)

    # Make the user the creator of this series so we isolate the coin-debit
    # path (no creator credit when the viewer IS the creator)
    await db_session.execute(update(Series).where(Series.id == series.id).values(creator_id=user_id))
    await db_session.execute(update(User).where(User.id == user_id).values(coins=100))
    await db_session.commit()

    resp = await client.post("/v1/entitlement/unlock", json={
        "episodeId": ep3.id,
        "source": "coins",
    }, headers=auth_headers(user_id))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["source"] == "coins"
    assert body["coinsAfter"] == 75  # 100 - 25 unlock cost


@pytest.mark.asyncio
async def test_unlock_with_insufficient_coins_403s(client, db_session):
    user_id, _ = await _signup(client, "penniless@example.com")
    series, ep3 = await _make_series(db_session, slug="unlockpoor", free_episodes=0)
    await db_session.execute(update(User).where(User.id == user_id).values(coins=10))
    await db_session.commit()

    resp = await client.post("/v1/entitlement/unlock", json={
        "episodeId": ep3.id,
        "source": "coins",
    }, headers=auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["error"] == "insufficient_coins"


@pytest.mark.asyncio
async def test_unlock_with_unknown_source_returns_501(client, db_session):
    user_id, _ = await _signup(client, "bad-source@example.com")
    series, ep3 = await _make_series(db_session, slug="unlockbadsrc", free_episodes=0)
    resp = await client.post("/v1/entitlement/unlock", json={
        "episodeId": ep3.id,
        "source": "bitcoin",
    }, headers=auth_headers(user_id))
    assert resp.status_code == 501
    assert resp.json()["error"] == "not_implemented"
