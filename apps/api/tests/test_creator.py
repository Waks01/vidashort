"""Creator tests — role enforcement, series create/update/submit, earnings math."""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import update, insert, select

from app.db.models import Series, Episode
from tests.conftest import auth_headers, _current as _email_cap


async def _create_creator(client, email="creator@example.com", name="Creator User"):
    """Sign up + verify OTP + manually promote to creator role (the real
    role-pick happens during onboarding — tests skip that for brevity).
    Returns the user id."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email,
        "password": "creatorpass1!",
        "name": name,
    })
    assert resp.status_code == 202, resp.text
    code = _email_cap().otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()["user"]["id"]


async def _make_existing_series(db_session, *, slug="owned-by-creator",
                                 creator_id="creator-id-placeholder"):
    series = Series(
        id=str(uuid.uuid4()),
        slug=slug,
        title="Owned By Creator",
        synopsis="",
        cover_url="",
        category="drama",
        language="en",
        source="creator",
        creator_id=creator_id,
        is_published=False,
        free_episodes=3,
        total_episodes=5,
    )
    db_session.add(series)
    for n in range(1, 6):
        ep = Episode(
            id=str(uuid.uuid4()),
            series_id=series.id,
            number=n,
            title=f"Ep {n}",
            synopsis="",
            duration_s=0,
            video_uid=None,
            video_ready=False,
            required_coins=25,
            is_free=False,
        )
        db_session.add(ep)
    await db_session.commit()
    return series


# -------- profile --------

@pytest.mark.asyncio
async def test_creator_profile_403_for_viewer(client):
    vu = await _create_creator(client, "viewer-creator@example.com", name="Viewer")
    resp = await client.get("/v1/creator/profile", headers=auth_headers(vu))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_creator_profile_returns_profile_when_role_matches(client, db_session):
    creator_id = await _create_creator(client, "profile-creator@example.com")

    # Promote to creator role by directly updating the User row
    from app.db.models import User
    await db_session.execute(update(User).where(User.id == creator_id).values(role="creator"))
    await db_session.commit()

    resp = await client.get("/v1/creator/profile", headers=auth_headers(creator_id, role="creator"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["userId"] == creator_id
    assert body["name"] == "Creator User"


# -------- series create + upload URLs --------

@pytest.mark.asyncio
async def test_create_series_returns_draft_and_upload_urls(client, db_session):
    creator_id = await _create_creator(client, "series-creator@example.com")
    from app.db.models import User
    await db_session.execute(update(User).where(User.id == creator_id).values(role="creator"))
    await db_session.commit()

    resp = await client.post("/v1/creator/series", json={
        "title": "My New Drama",
        "synopsis": "Exciting plot",
        "category": "drama",
        "language": "en",
        "tags": ["romance", "drama"],
        "totalEpisodes": 3,
    }, headers=auth_headers(creator_id, role="creator"))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["series"]["totalEpisodes"] == 3
    assert body["series"]["moderationStatus"] == "draft"
    assert body["series"]["isPublished"] is False
    assert len(body["uploadUrls"]) == 3
    assert all("videoUploadUrl" in u for u in body["uploadUrls"])


# -------- update ownership / publish-state rules --------

@pytest.mark.asyncio
async def test_update_series_403_for_non_owner(client, db_session):
    # Series owned by someone else
    s = await _make_existing_series(db_session, slug="not-yours", creator_id="someone-else")
    other_creator = await _create_creator(client, "intruder@example.com")

    resp = await client.patch(
        f"/v1/creator/series/{s.id}",
        json={"title": "Hijacked"},
        headers=auth_headers(other_creator, role="creator"),
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "forbidden"


@pytest.mark.asyncio
async def test_update_series_409_when_already_published(client, db_session):
    creator_id = await _create_creator(client, "publocker@example.com")
    s = await _make_existing_series(db_session, slug="already-pub", creator_id=creator_id)
    await db_session.execute(update(Series).where(Series.id == s.id).values(is_published=True))
    await db_session.commit()

    resp = await client.patch(
        f"/v1/creator/series/{s.id}",
        json={"title": "Try to edit"},
        headers=auth_headers(creator_id, role="creator"),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "already_published"


# -------- submit-for-review --------

@pytest.mark.asyncio
async def test_submit_for_review_400_when_videos_still_processing(client, db_session):
    creator_id = await _create_creator(client, "submitter@example.com")
    s = await _make_existing_series(db_session, slug="uploading", creator_id=creator_id)
    # Series has episodes with video_ready=False

    resp = await client.post(
        f"/v1/creator/series/{s.id}/submit-for-review",
        headers=auth_headers(creator_id, role="creator"),
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "videos_processing"


@pytest.mark.asyncio
async def test_submit_for_review_succeeds_when_videos_ready(client, db_session):
    creator_id = await _create_creator(client, "submitsuccess@example.com")
    s = await _make_existing_series(db_session, slug="ready-to-go", creator_id=creator_id)
    # Mark all episodes as ready
    await db_session.execute(
        update(Episode).where(Episode.series_id == s.id).values(video_ready=True)
    )
    await db_session.commit()

    resp = await client.post(
        f"/v1/creator/series/{s.id}/submit-for-review",
        headers=auth_headers(creator_id, role="creator"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["moderation_status"] == "pending"


# -------- payout min (locked ₦5,000 = 50,000 coins per CLAUDE.md §4) --------

@pytest.mark.asyncio
async def test_request_payout_rejects_below_minimum(client):
    creator_id = await _create_creator(client, "payout-fail@example.com")
    resp = await client.post("/v1/creator/payouts", json={
        "amount_coins": 1000,  # way below ₦5,000
    }, headers=auth_headers(creator_id, role="creator"))
    assert resp.status_code == 400
    assert resp.json()["error"] == "below_minimum"


@pytest.mark.asyncio
async def test_request_payout_accepts_exactly_minimum(client, db_session):
    creator_id = await _create_creator(client, "payout-ok@example.com")
    # Seed some earnings so the payout request is within available balance.
    from app.db.models import CreatorEarning
    db_session.add(CreatorEarning(
        id=str(uuid.uuid4()),
        creator_id=creator_id,
        episode_id=str(uuid.uuid4()),
        gross_coins=100000,
        creator_coins=60000,
    ))
    await db_session.commit()

    resp = await client.post("/v1/creator/payouts", json={
        "amount_coins": 50000,  # exactly ₦5,000
    }, headers=auth_headers(creator_id, role="creator"))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    payout = body["payout"]
    assert payout["amountCoins"] == 50000
    assert payout["amountNaira"] == 5000.0
    assert payout["status"] == "pending"
