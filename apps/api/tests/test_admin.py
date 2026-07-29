"""Admin tests — role enforcement + moderation/payout decisions."""
import uuid
import json
from datetime import datetime

import pytest
from sqlalchemy import insert

from app.db.models import Series, ModerationItem, PayoutRequest
from tests.conftest import auth_headers, _current as _email_cap


async def _signup(client, email):
    """Sign up + verify OTP, return the user id."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email,
        "password": "adminpass123!",
        "name": "Admin User",
    })
    assert resp.status_code == 202, resp.text
    code = _email_cap().otp_calls[-1]["code"]
    verify = await client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert verify.status_code == 200, verify.text
    return verify.json()["user"]["id"]


@pytest.mark.asyncio
async def test_admin_overview_403_for_viewer(client):
    viewer_id = await _signup(client, "viewer-admin-test@example.com")
    resp = await client.get("/v1/admin/overview", headers=auth_headers(viewer_id))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_overview_returns_zero_stats_for_fresh_db(client, db_session):
    admin_id = await _signup(client, "admin1@example.com")
    # Promote to admin role
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    resp = await client.get("/v1/admin/overview", headers=auth_headers(admin_id, role="admin"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["gmvNaira"] == 0.0
    assert body["dau"] == 0
    assert body["moderationQueueSize"] == 0


@pytest.mark.asyncio
async def test_moderation_decide_approve_publishes_series(client, db_session):
    admin_id = await _signup(client, "admin-mod@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    # Create a series + a moderation item for it
    series = Series(
        id=str(uuid.uuid4()),
        slug="needs-approval",
        title="Awaiting Approval",
        synopsis="",
        cover_url="",
        category="drama",
        language="en",
        source="creator",
        creator_id=None,
        is_published=False,
        moderation_status="pending",
        free_episodes=3,
        total_episodes=5,
    )
    db_session.add(series)
    await db_session.flush()
    item = ModerationItem(
        id=str(uuid.uuid4()),
        kind="series",
        ref_id=series.id,
        reason="creator-submitted",
        status="pending",
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.post(
        f"/v1/admin/moderation/{item.id}/decide",
        json={"decision": "approve", "note": "looks good"},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["status"] == "approved"

    # Verify the series got published — refetch via SELECT with populate_existing so we see
    # the commit made by the HTTP handler (different session).
    from sqlalchemy import select as _select
    refreshed = (await db_session.execute(
        _select(Series).where(Series.id == series.id).execution_options(populate_existing=True)
    )).scalar_one()
    assert refreshed.is_published is True
    assert refreshed.moderation_status == "approved"


@pytest.mark.asyncio
async def test_moderation_decide_rejects_invalid_decision(client, db_session):
    admin_id = await _signup(client, "admin-bad-dec@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    item = ModerationItem(
        id=str(uuid.uuid4()),
        kind="account",
        ref_id="some-user-id",
        reason="test",
        status="pending",
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.post(
        f"/v1/admin/moderation/{item.id}/decide",
        json={"decision": "maybe"},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_decision"


@pytest.mark.asyncio
async def test_content_update_404_for_missing_series(client, db_session):
    admin_id = await _signup(client, "admin-cu@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    resp = await client.patch(
        f"/v1/admin/content/{uuid.uuid4()}",
        json={"category": "horror"},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_content_update_changes_category_and_logs_audit(client, db_session):
    admin_id = await _signup(client, "admin-cu2@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    series = Series(
        id=str(uuid.uuid4()),
        slug="to-edit", title="Edit Me", synopsis="",
        cover_url="", category="drama", language="en",
        source="creator", creator_id=None,
        is_published=False, free_episodes=3, total_episodes=5,
    )
    db_session.add(series)
    await db_session.commit()

    resp = await client.patch(
        f"/v1/admin/content/{series.id}",
        json={"category": "horror", "isVipOnly": True},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 200, resp.text

    from sqlalchemy import select as _select
    refreshed = (await db_session.execute(
        _select(Series).where(Series.id == series.id).execution_options(populate_existing=True)
    )).scalar_one()
    assert refreshed.category == "horror"
    assert refreshed.is_vip_only is True


@pytest.mark.asyncio
async def test_user_update_ban_and_refund_coins(client, db_session):
    admin_id = await _signup(client, "admin-ban@example.com")
    target_id = await _signup(client, "target-ban@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    # Grant the target 100 coins first so the refund is visible
    await db_session.execute(update(User).where(User.id == target_id).values(coins=100))
    await db_session.commit()

    resp = await client.patch(
        f"/v1/admin/users/{target_id}",
        json={"banned": True, "refundCoins": 50, "banReason": "abuse"},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 200, resp.text

    from sqlalchemy import select as _select
    UserModel = __import__("app.db.models", fromlist=["User"]).User
    refreshed = (await db_session.execute(
        _select(UserModel).where(UserModel.id == target_id).execution_options(populate_existing=True)
    )).scalar_one()
    assert refreshed.banned_at is not None
    assert refreshed.ban_reason == "abuse"
    assert refreshed.coins == 150  # 100 + 50 refund


@pytest.mark.asyncio
async def test_payout_decide_approve_moves_status(client, db_session):
    admin_id = await _signup(client, "admin-pay@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    payout = PayoutRequest(
        id=str(uuid.uuid4()),
        creator_id="creator-x",
        amount_coins=50000,
        amount_naira=5000.0,
        status="pending",
        payout_method="Bank",
        payout_account="0123456789",
    )
    db_session.add(payout)
    await db_session.commit()

    resp = await client.post(
        f"/v1/admin/payouts/{payout.id}/decide",
        json={"decision": "approve", "note": "verified bank"},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "approved"

    from sqlalchemy import select as _select
    refreshed = (await db_session.execute(
        _select(PayoutRequest).where(PayoutRequest.id == payout.id).execution_options(populate_existing=True)
    )).scalar_one()
    assert refreshed.status == "approved"
    assert refreshed.note == "verified bank"


@pytest.mark.asyncio
async def test_payout_decide_409_when_already_decided(client, db_session):
    admin_id = await _signup(client, "admin-pay2@example.com")
    from app.db.models import User
    from sqlalchemy import update
    await db_session.execute(update(User).where(User.id == admin_id).values(role="admin"))
    await db_session.commit()

    payout = PayoutRequest(
        id=str(uuid.uuid4()),
        creator_id="creator-y",
        amount_coins=50000,
        amount_naira=5000.0,
        status="approved",  # already decided
        payout_method="OPay",
        payout_account="xyz",
    )
    db_session.add(payout)
    await db_session.commit()

    resp = await client.post(
        f"/v1/admin/payouts/{payout.id}/decide",
        json={"decision": "reject", "note": "double-check"},
        headers=auth_headers(admin_id, role="admin"),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "already_decided"
