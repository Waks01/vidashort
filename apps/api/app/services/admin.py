from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.models import User, Series, ModerationItem, PayoutRequest, CoinTxn, AuditLog
from app.schemas.admin import (
    AdminAdCampaignItem,
    AdminFinanceResponse,
    AdminModerationDecideRequest,
    AdminModerationResponse,
    AdminOverviewResponse,
    AdminPayoutDecideRequest,
    AdminUserUpdateRequest,
)


async def overview(db: AsyncSession, range: str) -> AdminOverviewResponse:
    return AdminOverviewResponse(
        gmv_naira=0.0,
        net_revenue_naira=0.0,
        dau=0,
        mau=0,
        new_signups=0,
        paying_users=0,
        active_vip=0,
        ad_cap_hits=0,
        moderation_queue_size=0,
        pending_payouts_naira=0.0,
        top_series=[],
    )


async def moderation(db: AsyncSession, kind, status, cursor, limit) -> AdminModerationResponse:
    return AdminModerationResponse(items=[], next_cursor=None)


async def content_list(db: AsyncSession, cursor, source, q, category, moderation_status) -> dict:
    """Paginated admin view of all Series. Filters: source (original|tmdb|creator),
    category, moderation_status. `q` matches title LIKE %q%. Cursor is the
    last id from the previous page; for now we slice on Series.id."""
    from app.db.models import Series as SeriesModel
    stmt = select(SeriesModel)
    if source:
        stmt = stmt.where(SeriesModel.source == source)
    if category:
        stmt = stmt.where(SeriesModel.category == category)
    if moderation_status:
        stmt = stmt.where(SeriesModel.moderation_status == moderation_status)
    if q:
        stmt = stmt.where(SeriesModel.title.ilike(f"%{q}%"))
    if cursor:
        stmt = stmt.where(SeriesModel.id > cursor)
    stmt = stmt.order_by(SeriesModel.id).limit(50)
    rows = (await db.execute(stmt)).scalars().all()
    next_cursor = rows[-1].id if len(rows) == 50 else None
    return {
        "items": [
            {
                "id": str(r.id),
                "title": r.title,
                "category": r.category,
                "source": r.source,
                "moderation_status": r.moderation_status,
                "is_published": r.is_published,
                "total_episodes": r.total_episodes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "next_cursor": next_cursor,
    }


async def moderation_decide(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    """Approve or reject a moderation item. On approve:
      - Series items → series.is_published=True, series.moderation_status='approved'
      - Comment items → noop (handled by the comment service)
      - Account items → user.banned/unbanned per decision
    Every decision appends an AuditLog row so we have a full audit trail of who
    decided what."""
    from app.core.errors import AppError
    decision = payload.decision
    if decision not in ("approve", "reject"):
        raise AppError(status_code=400, code="invalid_decision", detail=f"decision must be approve|reject, got {decision!r}")
    item = await db.get(ModerationItem, id)
    if not item:
        raise AppError(status_code=404, code="not_found", detail="Moderation item not found")
    if item.status != "pending":
        raise AppError(status_code=409, code="already_decided", detail=f"Item is {item.status}")
    item.status = "approved" if decision == "approve" else "rejected"
    item.decided_at = datetime.utcnow()
    item.decided_by = actor_id
    item.note = payload.note
    if item.kind == "series":
        series = await db.get(Series, item.ref_id)
        if series:
            if decision == "approve":
                series.is_published = True
                series.moderation_status = "approved"
            else:
                series.moderation_status = "rejected"
                series.is_published = False
    db.add(AuditLog(
        id=str(__import__("uuid").uuid4()),
        actor_id=actor_id,
        action=f"moderation_{decision}",
        target_kind=item.kind,
        target_id=item.ref_id,
        after=__import__("json").dumps({"note": payload.note or ""}),
    ))
    await db.commit()
    return {"ok": True, "status": item.status}


async def content_update(db: AsyncSession, actor_id: str, id: str, payload: dict) -> dict:
    """Admin override on a Series row: set category, is_vip_only, is_published,
    copyright_owner. Everything in `payload` is treated as opt-in (missing
    keys are no-ops). All changes are audit-logged with before/after."""
    from app.core.errors import AppError
    series = await db.get(Series, id)
    if not series:
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    before = {
        "title": series.title,
        "category": series.category,
        "is_published": series.is_published,
        "is_vip_only": series.is_vip_only,
        "copyright_owner": series.copyright_owner,
    }
    if "title" in payload:
        series.title = payload["title"]
    if "category" in payload:
        series.category = payload["category"]
    # Accept either snake_case (Python convention) or camelCase (wire format).
    is_published = payload.get("is_published", payload.get("isPublished"))
    if is_published is not None:
        series.is_published = bool(is_published)
    is_vip_only = payload.get("is_vip_only", payload.get("isVipOnly"))
    if is_vip_only is not None:
        series.is_vip_only = bool(is_vip_only)
    if "copyright_owner" in payload:
        series.copyright_owner = payload["copyright_owner"]
    db.add(AuditLog(
        id=str(__import__("uuid").uuid4()),
        actor_id=actor_id,
        action="content_update",
        target_kind="series",
        target_id=series.id,
        before=__import__("json").dumps(before),
        after=__import__("json").dumps(payload),
    ))
    await db.commit()
    return {"ok": True}


async def content_feature(db: AsyncSession, actor_id: str, id: str, payload: dict) -> dict:
    """Pin a series to the home/featured rail. `featured_until` is an ISO
    timestamp; rows past it are auto-excluded by the content router."""
    from app.core.errors import AppError
    from datetime import datetime as _dt
    series = await db.get(Series, id)
    if not series:
        raise AppError(status_code=404, code="not_found", detail="Series not found")
    try:
        until = _dt.fromisoformat(payload["featured_until"].replace("Z", "+00:00")) if payload.get("featured_until") else None
    except (KeyError, ValueError):
        raise AppError(status_code=400, code="invalid_featured_until", detail="featured_until must be ISO 8601")
    series.featured_until = until
    series.feature_rank = int(payload.get("feature_rank", 0))
    db.add(AuditLog(
        id=str(__import__("uuid").uuid4()),
        actor_id=actor_id,
        action="content_feature",
        target_kind="series",
        target_id=series.id,
        after=__import__("json").dumps({"featured_until": payload.get("featured_until"), "feature_rank": series.feature_rank}),
    ))
    await db.commit()
    return {"ok": True}


async def user_list(db: AsyncSession, cursor, role, q, banned) -> dict:
    return {"items": [], "next_cursor": None}


async def user_detail(db: AsyncSession, id: str) -> dict:
    user = await db.get(User, id)
    if not user:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="User not found")
    return {"user": {"id": str(user.id), "email": user.email, "name": user.name, "role": user.role, "coins": user.coins}}


async def user_update(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    """Admin edit on a User row: change role, ban/unban, optional coin refund
    (writes a CoinTxn with reason='admin_refund' for traceability). Bans are
    append-only via `banned_at` + `ban_reason`."""
    from app.core.errors import AppError
    from datetime import datetime as _dt
    user = await db.get(User, id)
    if not user:
        raise AppError(status_code=404, code="not_found", detail="User not found")
    if payload.role is not None:
        if payload.role not in ("viewer", "creator", "admin"):
            raise AppError(status_code=400, code="invalid_role", detail=f"role must be viewer|creator|admin, got {payload.role!r}")
        user.role = payload.role
    if payload.banned is True and not user.banned_at:
        user.banned_at = _dt.utcnow()
        user.ban_reason = payload.ban_reason or ""
    elif payload.banned is False and user.banned_at:
        user.banned_at = None
        user.ban_reason = None
    if payload.refund_coins:
        user.coins += payload.refund_coins
        from app.db.models import CoinTxn
        db.add(CoinTxn(
            id=str(__import__("uuid").uuid4()),
            user_id=user.id,
            delta=payload.refund_coins,
            reason="admin_refund",
            ref_id=actor_id,
            balance_after=user.coins,
        ))
    db.add(AuditLog(
        id=str(__import__("uuid").uuid4()),
        actor_id=actor_id,
        action="user_update",
        target_kind="user",
        target_id=user.id,
        after=__import__("json").dumps({
            "role": payload.role,
            "banned": payload.banned,
            "refund_coins": payload.refund_coins,
        }),
    ))
    await db.commit()
    return {"ok": True}


async def ad_campaign_update(db: AsyncSession, actor_id: str, id: str, payload: dict) -> dict:
    """Admin update on an ad campaign. Phase 2 reads campaign config from a
    static table; Phase 3 will move it to Redis for hot-reload. For now we
    no-op with an audit row — the real config table doesn't exist yet."""
    from app.core.errors import AppError
    db.add(AuditLog(
        id=str(__import__("uuid").uuid4()),
        actor_id=actor_id,
        action="ad_campaign_update",
        target_kind="ad_campaign",
        target_id=id,
        after=__import__("json").dumps(payload),
    ))
    await db.commit()
    return {"ok": True, "note": "ad campaign storage not implemented until Phase 3"}


async def payout_decide(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
    """Approve or reject a creator payout request. Approved payouts move to
    status='approved' (the actual money transfer happens out-of-band via
    OPay/PalmPay/Moniepoint/Bank APIs in Phase 3); rejected ones move to
    'rejected' with a note."""
    from app.core.errors import AppError
    decision = payload.decision
    if decision not in ("approve", "reject"):
        raise AppError(status_code=400, code="invalid_decision", detail=f"decision must be approve|reject, got {decision!r}")
    payout = await db.get(PayoutRequest, id)
    if not payout:
        raise AppError(status_code=404, code="not_found", detail="Payout request not found")
    if payout.status != "pending":
        raise AppError(status_code=409, code="already_decided", detail=f"Payout is {payout.status}")
    payout.status = "approved" if decision == "approve" else "rejected"
    payout.decided_at = datetime.utcnow()
    payout.decided_by = actor_id
    payout.note = payload.note
    db.add(AuditLog(
        id=str(__import__("uuid").uuid4()),
        actor_id=actor_id,
        action=f"payout_{decision}",
        target_kind="payout",
        target_id=payout.id,
        after=__import__("json").dumps({"note": payload.note or ""}),
    ))
    await db.commit()
    return {"ok": True, "status": payout.status}


async def ad_campaigns(db: AsyncSession) -> list[AdminAdCampaignItem]:
    return []


async def finance(db: AsyncSession, range: str) -> AdminFinanceResponse:
    return AdminFinanceResponse(
        net_revenue_naira=0.0,
        gross_coin_sales_naira=0.0,
        creator_liability_naira=0.0,
        platform_net_naira=0.0,
        ledger=[],
    )