from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.models import User, Series, ModerationItem, PayoutRequest, CoinTxn, AuditLog, VipEntitlement, AdImpression, CreatorEarning
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
    now = datetime.utcnow()
    if range == "24h":
        since = now - timedelta(hours=24)
    elif range == "7d":
        since = now - timedelta(days=7)
    else:
        since = now - timedelta(days=30)
    
    new_signups = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= since)
    )).scalar_one()
    
    dau = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= now - timedelta(hours=24))
    )).scalar_one()
    
    mau = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= now - timedelta(days=30))
    )).scalar_one()
    
    paying = (await db.execute(
        select(func.count()).select_from(User).where(User.coins > 0)
    )).scalar_one()
    
    active_vip = (await db.execute(
        select(func.count()).select_from(VipEntitlement).where(VipEntitlement.expires_at > now)
    )).scalar_one()
    
    from app.services.ad_cap import DAILY_AD_CAP
    caps_result = await db.execute(
        select(func.count()).select_from(AdImpression)
        .where(AdImpression.created_at >= now.date())
        .group_by(AdImpression.user_id)
        .having(func.count() >= DAILY_AD_CAP)
    )
    caps = caps_result.scalar_one_or_none() or 0
    
    mod_queue = (await db.execute(
        select(func.count()).select_from(ModerationItem).where(ModerationItem.status == "pending")
    )).scalar_one()
    
    pending_result = await db.execute(
        select(func.sum(PayoutRequest.amount_coins)).where(PayoutRequest.status == "pending")
    )
    pending_coins = pending_result.scalar_one() or 0
    
    revenue_result = await db.execute(
        select(func.sum(CoinTxn.delta)).where(CoinTxn.reason == "purchase", CoinTxn.created_at >= since)
    )
    gross_coins = max(0, revenue_result.scalar_one() or 0)
    gross_naira = gross_coins / 10
    
    earnings_result = await db.execute(select(func.sum(CreatorEarning.creator_coins)))
    total_liability = earnings_result.scalar_one() or 0
    
    return AdminOverviewResponse(
        gmv_naira=gross_naira,
        net_revenue_naira=gross_naira - (total_liability / 10),
        dau=dau,
        mau=mau,
        new_signups=new_signups,
        paying_users=paying,
        active_vip=active_vip,
        ad_cap_hits=caps,
        moderation_queue_size=mod_queue,
        pending_payouts_naira=pending_coins / 10,
        top_series=[],
    )


async def moderation(db: AsyncSession, kind, status, cursor, limit) -> AdminModerationResponse:
    from app.db.models import Series as SeriesModel
    stmt = select(ModerationItem)
    if kind:
        stmt = stmt.where(ModerationItem.kind == kind)
    if status:
        stmt = stmt.where(ModerationItem.status == status)
    stmt = stmt.order_by(ModerationItem.created_at.desc()).limit(limit)
    items_result = await db.execute(stmt)
    items_list = []
    for item in items_result.scalars().all():
        title = None
        submitted_by = None
        if item.submitter_id:
            user = await db.get(User, str(item.submitter_id))
            if user:
                submitted_by = user.name
        if item.kind == "series":
            series = await db.get(SeriesModel, str(item.ref_id))
            if series:
                title = series.title
        items_list.append(AdminModerationItem(
            id=str(item.id),
            kind=item.kind,
            ref_id=str(item.ref_id),
            title=title,
            submitted_by=submitted_by,
            submitted_at=item.created_at.isoformat() if item.created_at else None,
            reason=item.reason or "",
            preview=None,
        ))
    return AdminModerationResponse(items=items_list, next_cursor=None)


async def content_list(db: AsyncSession, cursor, source, q, category, moderation_status) -> dict:
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
    if item.submitter_id:
        try:
            from app.services import notifications as notif_svc
            await notif_svc.queue_payout_decision(db, str(item.submitter_id), id, decision)
        except Exception:
            pass
    return {"ok": True, "status": item.status}


async def content_update(db: AsyncSession, actor_id: str, id: str, payload: dict) -> dict:
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
    from app.db.models import User as UserModel
    stmt = select(UserModel)
    if role:
        stmt = stmt.where(UserModel.role == role)
    if q:
        stmt = stmt.where(UserModel.name.ilike(f"%{q}%") | UserModel.email.ilike(f"%{q}%"))
    if banned is not None:
        if banned:
            stmt = stmt.where(UserModel.banned_at.isnot(None))
        else:
            stmt = stmt.where(UserModel.banned_at.is_(None))
    if cursor:
        stmt = stmt.where(UserModel.id > cursor)
    stmt = stmt.order_by(UserModel.id).limit(50)
    rows = (await db.execute(stmt)).scalars().all()
    next_cursor = rows[-1].id if len(rows) == 50 else None
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "coins": u.coins,
                "bannedAt": u.banned_at.isoformat() if u.banned_at else None,
            }
            for u in rows
        ],
        "next_cursor": next_cursor,
    }


async def user_detail(db: AsyncSession, id: str) -> dict:
    user = await db.get(User, id)
    if not user:
        from app.core.errors import AppError
        raise AppError(status_code=404, code="not_found", detail="User not found")
    return {"user": {"id": str(user.id), "email": user.email, "name": user.name, "role": user.role, "coins": user.coins}}


async def user_update(db: AsyncSession, actor_id: str, id: str, payload) -> dict:
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
    try:
        from app.services import notifications as notif_svc
        await notif_svc.queue_payout_decision(db, str(payout.user_id), id, decision)
    except Exception:
        pass
    return {"ok": True, "status": payout.status}


async def ad_campaigns(db: AsyncSession) -> list[AdminAdCampaignItem]:
    return []


async def finance(db: AsyncSession, range: str) -> AdminFinanceResponse:
    from datetime import timedelta
    
    now = datetime.utcnow()
    since = now - timedelta(days=30)
    if range == "7d":
        since = now - timedelta(days=7)
    elif range == "24h":
        since = now - timedelta(hours=24)
    
    sales_result = await db.execute(
        select(func.sum(CoinTxn.delta)).where(CoinTxn.reason == "purchase", CoinTxn.created_at >= since)
    )
    gross_coins = max(0, sales_result.scalar_one() or 0)
    
    earnings_result = await db.execute(
        select(func.sum(CreatorEarning.creator_coins)).where(CreatorEarning.created_at >= since)
    )
    creator_liability_coins = earnings_result.scalar_one() or 0
    
    gross_naira = gross_coins / 10
    creator_liability_naira = creator_liability_coins / 10
    
    ledger = []
    recent_txns = (await db.execute(
        select(CoinTxn).where(CoinTxn.created_at >= since).order_by(CoinTxn.created_at.desc()).limit(50)
    )).scalars().all()
    for t in recent_txns:
        ledger.append({
            "id": str(t.id),
            "type": t.reason,
            "delta": t.delta,
            "userId": str(t.user_id),
            "refId": str(t.ref_id) if t.ref_id else None,
            "createdAt": t.created_at.isoformat() if t.created_at else None,
        })
    
    return AdminFinanceResponse(
        net_revenue_naira=gross_naira - creator_liability_naira,
        gross_coin_sales_naira=gross_naira,
        creator_liability_naira=creator_liability_naira,
        platform_net_naira=gross_naira - creator_liability_naira,
        ledger=ledger,
    )