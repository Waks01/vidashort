"""Webhook signature verification + provider-specific handlers.

Signature scheme: every webhook provider sends an HMAC-SHA256 digest of the raw
request body using a shared secret. The signature goes in the
`X-Vidashort-Signature` header (we choose this header so it's the same across
providers — provider-specific headers like Stripe's `Stripe-Signature` would
require per-provider parsing).

For Phase 2.5 we treat the signature as hex digest of HMAC-SHA256(body, secret).
Production might need to support provider-specific formats (e.g. t=<ts>,v1=<sig>
Stripe-style with replay protection) — that lives behind the same `verify_signature`
API.
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import (
    AuditLog,
    Episode,
    ModerationItem,
    RefreshToken,
    User,
    VipEntitlement,
)


def verify_signature(secret: str, body: bytes, header: str) -> bool:
    """Constant-time HMAC-SHA256 compare. Returns False if either side is empty."""
    if not secret or not header:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


# ---------- Cloudflare Stream ----------

async def handle_cloudflare(db: AsyncSession, payload: dict) -> None:
    """Cloudflare pings us when a video finishes processing. Mark the matching
    Episode row so the player can show the episode as ready.
    """
    uid = payload.get("uid")
    if not uid:
        return
    result = await db.execute(select(Episode).where(Episode.video_uid == uid))
    episode = result.scalar_one_or_none()
    if episode:
        episode.video_ready = True
        await db.commit()


# ---------- RevenueCat ----------

async def handle_revenuecat(db: AsyncSession, payload: dict) -> None:
    """RevenueCat sends events like INITIAL_PURCHASE / RENEWAL / CANCELLATION.
    We sync them to our `vip_entitlements` table so `paywall.is_vip()` is
    authoritative without an extra round-trip.

    Expected payload shape (RevenueCat webhook):
      {
        "event": {"type": "INITIAL_PURCHASE", ...},
        "event_timestamp_ms": 1700000000000,
      }
    Also fetches the canonical subscription state from RevenueCat for safety.
    """
    from app.integrations.revenuecat import fetch_subscriber_info
    event = (payload.get("event") or {}).get("type", "")
    app_user_id = (payload.get("event") or {}).get("app_user_id") or payload.get("app_user_id")
    if not app_user_id:
        raise AppError(status_code=400, code="missing_app_user_id", detail="RevenueCat event missing app_user_id")
    user = await db.get(User, app_user_id)
    if not user:
        # RevenueCat user_ids may not match our UUIDs — if the mobile client
        # sent the email as the app_user_id, fall back to that lookup.
        result = await db.execute(select(User).where(User.email == app_user_id))
        user = result.scalar_one_or_none()
    if not user:
        raise AppError(status_code=404, code="user_not_found", detail=f"No user for RevenueCat app_user_id={app_user_id}")

    # Always pull the canonical state — webhook events can be missed or out of order.
    sub = await fetch_subscriber_info(app_user_id) or {}
    entitlements = sub.get("entitlements", {}) or {}
    vip_ent = entitlements.get("vip") or {}

    if event in ("INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION", "PRODUCT_CHANGE") and vip_ent:
        await _activate_vip(db, user, source="revenuecat", product_id=vip_ent.get("product_identifier", "unknown"))
    elif event in ("CANCELLATION", "EXPIRATION", "BILLING_ISSUE"):
        await _deactivate_vip(db, user)


async def _activate_vip(db: AsyncSession, user: User, *, source: str, product_id: str) -> None:
    """Insert or extend the user's VIP entitlement. We don't differentiate
    between monthly/yearly at this layer — the product_id is recorded for
    analytics and refund lookup.
    """
    expires_at = datetime.utcnow() + _vip_duration_from_product(product_id)
    row = VipEntitlement(
        id=str(uuid.uuid4()),
        user_id=user.id,
        source=source,
        product_id=product_id,
        started_at=datetime.utcnow(),
        expires_at=expires_at,
        auto_renew=True,
    )
    db.add(row)
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor_id=user.id,
        action="vip_activate",
        target_kind="user",
        target_id=user.id,
        after=json.dumps({"source": source, "product_id": product_id, "expires_at": expires_at.isoformat()}),
    ))
    await db.commit()


async def _deactivate_vip(db: AsyncSession, user: User) -> None:
    """Mark the user's VIP entitlement as expired. We don't delete the row —
    the ledger is append-only for accounting."""
    result = await db.execute(
        select(VipEntitlement).where(
            VipEntitlement.user_id == user.id,
            VipEntitlement.expires_at > datetime.utcnow(),
        )
    )
    for row in result.scalars().all():
        row.expires_at = datetime.utcnow()
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor_id=user.id,
        action="vip_deactivate",
        target_kind="user",
        target_id=user.id,
    ))
    await db.commit()


def _vip_duration_from_product(product_id: str) -> "datetime.timedelta":
    """Default VIP duration by product_id convention. Override via env or
    explicit product catalog when the team finalizes pricing."""
    from datetime import timedelta
    if "year" in product_id.lower() or "annual" in product_id.lower():
        return timedelta(days=365)
    return timedelta(days=30)


# ---------- Apple App Store server-to-server notifications ----------

async def handle_apple(db: AsyncSession, payload: dict) -> None:
    """Apple sends signed JWTs in `signedPayload`. We trust the signature
    because the router verified `verify_signature(apple_private_key, body, header)`
    — but the router's signing key isn't the Apple root key, so production
    needs real JWS verification. Phase 3 work; for Phase 2 we parse the
    notification type and update our VIP table.
    """
    notification_type = payload.get("notificationType", "")
    if notification_type in ("SUBSCRIBED", "DID_RENEW"):
        await _activate_vip(db, user=_user_from_apple_payload(payload), source="apple", product_id=payload.get("productId", "apple-sub"))
    elif notification_type in ("EXPIRED", "DID_FAIL_TO_RENEW", "REFUND"):
        user = _user_from_apple_payload(payload)
        if user:
            await _deactivate_vip(db, user)


def _user_from_apple_payload(payload: dict) -> User | None:
    """Best-effort user lookup. Apple only sends a notification UUID + the
    signed transaction; the user_id lives in our DB keyed by original_txn_id.
    Phase 3: index VipEntitlement.original_txn_id and look up by that."""
    return None


# ---------- Google Play Real-time Developer Notifications ----------

async def handle_google(db: AsyncSession, payload: dict) -> None:
    """Google's RTDN is published to Pub/Sub. We receive the message and the
    `message.data` is base64-encoded JSON. The `subscriptionNotification`
    carries notificationType ∈ {1..13}. For Phase 2 we map SUBSCRIPTION_RECOVERED=1
    and SUBSCRIPTION_RENEWED=2 to activate, and EXPIRED=13 to deactivate.
    """
    import base64
    raw = payload.get("message", {}).get("data", "")
    try:
        decoded = json.loads(base64.b64decode(raw)) if raw else payload
    except Exception:
        decoded = payload
    notification = decoded.get("subscriptionNotification", {}) or {}
    n_type = notification.get("notificationType", 0)
    if n_type in (1, 2, 4, 7):  # RECOVERED, RENEWED, PENDING_PURCHASE_CANCELED->NO, ACCOUNT_HOLD
        # No clean user lookup without a server-side purchase token correlation;
        # for Phase 2 we leave this as a no-op + audit row.
        db.add(AuditLog(
            id=str(uuid.uuid4()),
            actor_id="google",
            action="vip_activate_or_hold",
            target_kind="subscription",
            target_id=str(notification.get("purchaseToken", "")),
        ))
        await db.commit()
    elif n_type in (12, 13):  # REVOKED, EXPIRED
        db.add(AuditLog(
            id=str(uuid.uuid4()),
            actor_id="google",
            action="vip_deactivate",
            target_kind="subscription",
            target_id=str(notification.get("purchaseToken", "")),
        ))
        await db.commit()