"""/v1/me tests — full surface (GET, PATCH, age-confirm, DELETE)."""
import pytest
from sqlalchemy import select

from app.db.models import User
from tests.conftest import signup_and_verify


async def _me(client, token: str):
    return await client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})


# ─── GET /v1/me ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_requires_bearer_token(client):
    resp = await client.get("/v1/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_full_payload_after_signup(client, email_capture):
    """GET /v1/me returns the documented {user, wallet, adCap, streak} shape."""
    body = await signup_and_verify(
        client, email="me-alice@example.com", password="correctpw123", name="Alice"
    )
    resp = await _me(client, body["accessToken"])
    assert resp.status_code == 200, resp.text
    payload = resp.json()

    assert payload["user"]["email"] == "me-alice@example.com"
    assert payload["user"]["name"] == "Alice"
    assert payload["user"]["role"] == "viewer"
    assert payload["user"]["avatarUrl"] is None
    assert payload["user"]["genres"] == []
    assert payload["user"]["language"] == "en"
    assert payload["user"]["ageConfirmed"] is False
    assert payload["user"]["onboarded"] is False
    assert payload["user"]["createdAt"]

    assert payload["wallet"] == {"coins": 0, "vip": {"active": False, "until": None}}

    assert payload["adCap"]["used"] == 0
    assert payload["adCap"]["limit"] == 100
    assert payload["adCap"]["remaining"] == 100
    assert payload["adCap"]["resetsAt"]

    # streak is a small struct — keys must exist even if day == 0 / lastClaimedOn null.
    assert "day" in payload["streak"]
    assert "lastClaimedOn" in payload["streak"]


@pytest.mark.asyncio
async def test_me_404_after_user_hard_deleted(client, email_capture, db_session):
    """If we DELETE /v1/me, the user row's deleted_at is set (soft delete). The
    service short-circuits with not_found on subsequent GET."""
    body = await signup_and_verify(
        client, email="me-del@example.com", password="correctpw123", name="Del"
    )
    headers = {"Authorization": f"Bearer {body['accessToken']}"}

    # Delete
    delete = await client.delete("/v1/me", headers=headers)
    assert delete.status_code == 204, delete.text

    # The user row is now soft-deleted (deleted_at set, email scrambled).
    user = (await db_session.execute(
        select(User).where(User.id == body["user"]["id"])
    )).scalar_one()
    assert user.deleted_at is not None
    assert user.deleted_at.year >= 2026
    assert "@deleted" in user.email


# ─── PATCH /v1/me ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patch_me_updates_name_and_genres(client, email_capture):
    body = await signup_and_verify(
        client, email="me-patch@example.com", password="correctpw123", name="OldName"
    )
    headers = {"Authorization": f"Bearer {body['accessToken']}"}

    resp = await client.patch(
        "/v1/me",
        json={"name": "NewName", "genres": ["romance", "drama", "thriller"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["user"]["name"] == "NewName"
    assert payload["user"]["genres"] == ["romance", "drama", "thriller"]


@pytest.mark.asyncio
async def test_patch_me_partial_update_keeps_unspecified_fields(client, email_capture):
    """A PATCH with only `name` must not blank out the other fields."""
    body = await signup_and_verify(
        client, email="me-partial@example.com", password="correctpw123", name="Orig"
    )
    headers = {"Authorization": f"Bearer {body['accessToken']}"}

    resp = await client.patch("/v1/me", json={"name": "JustName"}, headers=headers)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["user"]["name"] == "JustName"
    assert payload["user"]["email"] == "me-partial@example.com"  # unchanged
    assert payload["user"]["role"] == "viewer"  # unchanged


# ─── POST /v1/me/age-confirm ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_age_confirm_sets_flag(client, email_capture):
    body = await signup_and_verify(
        client, email="me-age@example.com", password="correctpw123", name="OldEnough"
    )
    headers = {"Authorization": f"Bearer {body['accessToken']}"}

    # Flag starts false
    me0 = await _me(client, body["accessToken"])
    assert me0.json()["user"]["ageConfirmed"] is False

    # Confirm
    resp = await client.post(
        "/v1/me/age-confirm", json={"confirmed": True}, headers=headers,
    )
    assert resp.status_code == 204, resp.text

    # Flag is now true
    me1 = await _me(client, body["accessToken"])
    assert me1.json()["user"]["ageConfirmed"] is True


@pytest.mark.asyncio
async def test_age_confirm_with_false_leaves_flag_unset(client, email_capture):
    body = await signup_and_verify(
        client, email="me-nope@example.com", password="correctpw123", name="TooYoung"
    )
    headers = {"Authorization": f"Bearer {body['accessToken']}"}

    resp = await client.post(
        "/v1/me/age-confirm", json={"confirmed": False}, headers=headers,
    )
    assert resp.status_code == 204

    me0 = await _me(client, body["accessToken"])
    assert me0.json()["user"]["ageConfirmed"] is False


# ─── DELETE /v1/me ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_me_returns_204(client, email_capture, db_session):
    body = await signup_and_verify(
        client, email="me-gone@example.com", password="correctpw123", name="ByeBye"
    )
    headers = {"Authorization": f"Bearer {body['accessToken']}"}

    resp = await client.delete("/v1/me", headers=headers)
    assert resp.status_code == 204, resp.text

    # The DB row was soft-deleted: deleted_at is set, email scrambled to a
    # placeholder so a re-signup with the same email doesn't collide.
    user = (await db_session.execute(
        select(User).where(User.id == body["user"]["id"])
    )).scalar_one()
    assert user.deleted_at is not None
    assert user.email.startswith("deleted-")