"""Phase 2 verification — exact end-to-end sequence from docs/phases/02-backend-skeleton.md §Verification.

Walks the full sign-up → /v1/me → PATCH /v1/me → age-confirm → DELETE flow
against the in-process FastAPI app, asserting each step's documented
behaviour. This is the test version of the curl block in the spec; both
must stay in sync.
"""
import pytest
from sqlalchemy import select

from app.db.models import User
from tests.conftest import signup_and_verify


@pytest.mark.asyncio
async def test_phase2_end_to_end_flow(client, email_capture, db_session):
    """The exact flow the Phase 2 spec's verification section demonstrates.
    Each step's status code + a handful of payload assertions catches
    contract drift between the backend and the mobile client."""
    EMAIL = "phase2-e2e@example.com"
    PASSWORD = "correctpw123"

    # ── 1. POST /v1/auth/signup → 202 with {ok, requiresVerification}
    signup = await client.post("/v1/auth/signup", json={
        "email": EMAIL, "password": PASSWORD, "name": "Phase2E2E",
    })
    assert signup.status_code == 202, signup.text
    body = signup.json()
    assert body == {"ok": True, "requiresVerification": True}

    # The OTP was captured by the autouse email_capture fixture.
    code = email_capture.otp_calls[-1]["code"]
    assert len(code) == 6

    # ── 2. POST /v1/auth/otp/verify → 200 with AuthResponse
    verify = await client.post("/v1/auth/otp/verify", json={
        "email": EMAIL, "code": code,
    })
    assert verify.status_code == 200, verify.text
    auth = verify.json()
    assert "accessToken" in auth
    assert "refreshToken" in auth
    assert auth["user"]["email"] == EMAIL
    assert auth["user"]["role"] == "viewer"
    headers = {"Authorization": f"Bearer {auth['accessToken']}"}

    # ── 3. GET /v1/me → 200 with the documented {user, wallet, adCap, streak}
    me = await client.get("/v1/me", headers=headers)
    assert me.status_code == 200, me.text
    payload = me.json()
    assert payload["user"]["email"] == EMAIL
    assert payload["wallet"]["coins"] == 0
    assert payload["adCap"]["limit"] == 100
    assert payload["adCap"]["remaining"] == 100
    assert "streak" in payload

    # ── 4. PATCH /v1/me → 200 with updated fields
    patch = await client.patch(
        "/v1/me",
        json={"name": "Phase2E2E Updated", "genres": ["romance", "drama"]},
        headers=headers,
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["user"]["name"] == "Phase2E2E Updated"
    assert patch.json()["user"]["genres"] == ["romance", "drama"]

    # ── 5. POST /v1/me/age-confirm → 204 (no content)
    confirm = await client.post(
        "/v1/me/age-confirm", json={"confirmed": True}, headers=headers,
    )
    assert confirm.status_code == 204, confirm.text

    # ── 6. GET /v1/me → confirms ageConfirmed flipped to True
    me2 = await client.get("/v1/me", headers=headers)
    assert me2.json()["user"]["ageConfirmed"] is True

    # ── 7. DELETE /v1/me → 204 (soft-delete: row stays, deleted_at set)
    delete = await client.delete("/v1/me", headers=headers)
    assert delete.status_code == 204, delete.text

    # The user row is now soft-deleted and the email is scrambled so a
    # re-signup with the same address doesn't collide with the old row.
    user = (await db_session.execute(
        select(User).where(User.id == auth["user"]["id"])
    )).scalar_one()
    assert user.deleted_at is not None
    assert user.email.startswith("deleted-")