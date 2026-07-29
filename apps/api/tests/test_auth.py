"""Auth flow tests — signup (OTP-gated), signin, refresh, OTP, forgot/reset."""
import hashlib

import pytest
from sqlalchemy import select

from app.db.models import EmailOtp, PasswordReset, User


@pytest.mark.asyncio
async def test_health(client, fake_redis):
    """Sanity: the test client + dependency override wiring is alive."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["db"] == "ok"
    assert body["redis"] == "ok"


# ─── signup + OTP ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_signup_requires_verification_and_sends_otp(client, email_capture):
    """Signup is now 202 with requiresVerification=true (not 201 with tokens).
    It must send an OTP to the user."""
    resp = await client.post("/v1/auth/signup", json={
        "email": "alice@example.com",
        "password": "sup3rsecret!",
        "name": "Alice",
    })
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body == {"ok": True, "requiresVerification": True}
    assert len(email_capture.otp_calls) == 1
    assert email_capture.otp_calls[0]["to"] == "alice@example.com"
    assert len(email_capture.otp_calls[0]["code"]) == 6
    assert email_capture.otp_calls[0]["code"].isdigit()


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409(client, email_capture):
    await client.post("/v1/auth/signup", json={
        "email": "alice@example.com", "password": "sup3rsecret!", "name": "Alice",
    })
    dup = await client.post("/v1/auth/signup", json={
        "email": "alice@example.com", "password": "different", "name": "Alice 2",
    })
    assert dup.status_code == 409, dup.text


@pytest.mark.asyncio
async def test_verify_otp_mints_tokens_and_marks_verified(client, email_capture, db_session):
    signup = await client.post("/v1/auth/signup", json={
        "email": "bob@example.com", "password": "hunter2hunter", "name": "Bob",
    })
    assert signup.status_code == 202
    code = email_capture.otp_calls[0]["code"]

    verify = await client.post("/v1/auth/otp/verify", json={
        "email": "bob@example.com", "code": code,
    })
    assert verify.status_code == 200, verify.text
    body = verify.json()
    assert body["accessToken"]
    assert body["refreshToken"]
    assert body["user"]["email"] == "bob@example.com"

    # email_verified is now true on the user row.
    user = (await db_session.execute(
        select(User).where(User.email == "bob@example.com").execution_options(populate_existing=True)
    )).scalar_one()
    assert user.email_verified is True


@pytest.mark.asyncio
async def test_verify_otp_wrong_code_returns_400_and_counts_attempt(client, email_capture, db_session):
    await client.post("/v1/auth/signup", json={
        "email": "carol@example.com", "password": "password123!", "name": "Carol",
    })
    wrong = await client.post("/v1/auth/otp/verify", json={
        "email": "carol@example.com", "code": "000000",
    })
    assert wrong.status_code == 400
    assert wrong.json()["error"] == "invalid_code"

    otp = (await db_session.execute(
        select(EmailOtp).order_by(EmailOtp.created_at.desc()).execution_options(populate_existing=True)
    )).scalars().first()
    assert otp.attempts == 1


@pytest.mark.asyncio
async def test_verify_otp_lockout_after_5_failures(client, email_capture, db_session):
    await client.post("/v1/auth/signup", json={
        "email": "dan@example.com", "password": "password123!", "name": "Dan",
    })
    code = email_capture.otp_calls[0]["code"]

    # 4 wrong attempts — should still leave the OTP usable.
    for _ in range(4):
        r = await client.post("/v1/auth/otp/verify", json={
            "email": "dan@example.com", "code": "000000",
        })
        assert r.status_code == 400
    # 5th wrong attempt hits the lockout threshold — the OTP gets invalidated.
    locked = await client.post("/v1/auth/otp/verify", json={
        "email": "dan@example.com", "code": "000000",
    })
    assert locked.status_code == 400

    # Even the correct code is now rejected — the row was burned.
    after = await client.post("/v1/auth/otp/verify", json={
        "email": "dan@example.com", "code": code,
    })
    assert after.status_code == 400
    assert after.json()["error"] == "invalid_code"


@pytest.mark.asyncio
async def test_otp_resend_invalidates_previous(client, email_capture):
    await client.post("/v1/auth/signup", json={
        "email": "eve@example.com", "password": "password123!", "name": "Eve",
    })
    first_code = email_capture.otp_calls[0]["code"]

    resend = await client.post("/v1/auth/otp/resend", json={"email": "eve@example.com"})
    assert resend.status_code == 202
    second_code = email_capture.otp_calls[-1]["code"]
    assert second_code != first_code

    # The original code is now invalidated.
    first = await client.post("/v1/auth/otp/verify", json={
        "email": "eve@example.com", "code": first_code,
    })
    assert first.status_code == 400

    # The latest code works.
    second = await client.post("/v1/auth/otp/verify", json={
        "email": "eve@example.com", "code": second_code,
    })
    assert second.status_code == 200


@pytest.mark.asyncio
async def test_otp_resend_for_unknown_email_returns_202(client, email_capture):
    """Don't leak whether the email exists — both branches return 202 {ok:true}."""
    r = await client.post("/v1/auth/otp/resend", json={"email": "ghost@example.com"})
    assert r.status_code == 202
    assert r.json() == {"ok": True}
    assert email_capture.otp_calls == []


# ─── signin / refresh ────────────────────────────────────────────────────────


async def _signup_and_verify(client, email_capture, *, email: str, password: str, name: str) -> dict:
    """Helper: full signup + OTP verification. Returns the AuthResponse dict."""
    await client.post("/v1/auth/signup", json={"email": email, "password": password, "name": name})
    code = email_capture.otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()


@pytest.mark.asyncio
async def test_signin_then_refresh_rotates_tokens(client, email_capture):
    body = await _signup_and_verify(client, email_capture,
                                    email="frank@example.com", password="hunter2hunter", name="Frank")
    refresh_token = body["refreshToken"]

    refresh_resp = await client.post("/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert refresh_resp.status_code == 200, refresh_resp.text
    new_pair = refresh_resp.json()
    assert new_pair["refreshToken"] != refresh_token
    assert new_pair["user"]["email"] == "frank@example.com"

    # The OLD refresh must now be rejected — marked used_at, can't rotate twice.
    replay = await client.post("/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert replay.status_code == 401, replay.text


@pytest.mark.asyncio
async def test_refresh_replay_burns_all_user_tokens(client, email_capture):
    body = await _signup_and_verify(client, email_capture,
                                    email="greta@example.com", password="password123!", name="Greta")
    r1 = body["refreshToken"]

    first = await client.post("/v1/auth/refresh", json={"refreshToken": r1})
    r2 = first.json()["refreshToken"]

    replay = await client.post("/v1/auth/refresh", json={"refreshToken": r1})
    assert replay.status_code == 401

    second_replay = await client.post("/v1/auth/refresh", json={"refreshToken": r2})
    assert second_replay.status_code == 401, second_replay.text


@pytest.mark.asyncio
async def test_signin_wrong_password_returns_400(client, email_capture):
    await _signup_and_verify(client, email_capture,
                             email="henry@example.com", password="rightpass", name="Henry")
    bad = await client.post("/v1/auth/signin", json={
        "email": "henry@example.com", "password": "wrongpass",
    })
    assert bad.status_code == 400
    assert bad.json()["error"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_signin_blocked_until_verified(client, email_capture):
    """A user who signed up but never verified cannot sign in."""
    await client.post("/v1/auth/signup", json={
        "email": "ivy@example.com", "password": "password123!", "name": "Ivy",
    })
    r = await client.post("/v1/auth/signin", json={
        "email": "ivy@example.com", "password": "password123!",
    })
    assert r.status_code == 403
    assert r.json()["error"] == "email_unverified"


# ─── forgot / reset ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_forgot_returns_ok_regardless_of_email_existence(client, email_capture):
    real = await client.post("/v1/auth/forgot", json={"email": "real@example.com"})
    fake = await client.post("/v1/auth/forgot", json={"email": "never-registered@example.com"})
    assert real.status_code == 202
    assert fake.status_code == 202
    assert real.json() == {"ok": True} and fake.json() == {"ok": True}


@pytest.mark.asyncio
async def test_forgot_sends_deep_link_email(client, email_capture):
    await _signup_and_verify(client, email_capture,
                             email="jack@example.com", password="password123!", name="Jack")
    email_capture.reset_calls.clear()

    await client.post("/v1/auth/forgot", json={"email": "jack@example.com"})
    assert len(email_capture.reset_calls) == 1
    link = email_capture.reset_calls[0]["deep_link"]
    assert link.startswith("vidashort://reset-password?token=")
    raw_token = link.split("=", 1)[1]
    assert len(raw_token) > 20  # secrets.token_urlsafe(32) → ~43 chars


@pytest.mark.asyncio
async def test_reset_with_valid_token_changes_password(client, email_capture):
    await _signup_and_verify(client, email_capture,
                             email="kate@example.com", password="oldpass1!", name="Kate")
    email_capture.reset_calls.clear()
    await client.post("/v1/auth/forgot", json={"email": "kate@example.com"})
    raw_token = email_capture.reset_calls[0]["deep_link"].split("=", 1)[1]

    # Reset using the raw token from the email.
    reset = await client.post("/v1/auth/reset", json={
        "token": raw_token,
        "new_password": "newpass1!",
    })
    assert reset.status_code == 200
    assert reset.json() == {"ok": True}

    # Old password no longer works.
    old = await client.post("/v1/auth/signin", json={
        "email": "kate@example.com", "password": "oldpass1!",
    })
    assert old.status_code == 400

    # New password works.
    new = await client.post("/v1/auth/signin", json={
        "email": "kate@example.com", "password": "newpass1!",
    })
    assert new.status_code == 200


@pytest.mark.asyncio
async def test_reset_with_invalid_token_silent_ok(client, email_capture):
    await _signup_and_verify(client, email_capture,
                             email="liam@example.com", password="password123!", name="Liam")
    reset = await client.post("/v1/auth/reset", json={
        "token": "bogus-token-that-doesnt-exist",
        "new_password": "newpass1!",
    })
    assert reset.status_code == 200
    assert reset.json() == {"ok": True}

    # Sign-in with the original password still works.
    ok = await client.post("/v1/auth/signin", json={
        "email": "liam@example.com", "password": "password123!",
    })
    assert ok.status_code == 200


# ─── /v1/me ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_requires_bearer_token(client):
    resp = await client.get("/v1/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user_payload_after_signin(client, email_capture):
    body = await _signup_and_verify(client, email_capture,
                                    email="mia@example.com", password="supersecret", name="Mia")
    token = body["accessToken"]
    me = await client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    payload = me.json()
    assert payload["user"]["email"] == "mia@example.com"
    assert payload["wallet"]["coins"] == 0
    assert payload["adCap"]["limit"] == 100
