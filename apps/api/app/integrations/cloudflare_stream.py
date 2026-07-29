"""Cloudflare Stream integration.

Playback URLs are time-limited: a client gets a signed manifest URL with TTL
(default 1h, per CLAUDE.md §"How the three apps talk"), then Cloudflare serves
the HLS manifest. The signature prevents URL sharing beyond the TTL.

The signing scheme: HMAC-SHA256 of "{uid}:{exp}" using `settings.cf_stream_signing_key`
as the shared secret. Result is base64url-encoded and appended as the
`?signature=...` query parameter.

Upload URLs use Cloudflare's TUS direct-upload endpoint with a per-upload token
returned by their API. For Phase 2.5 we generate a placeholder URL — wiring up
the real Cloudflare Stream API call (`/accounts/{id}/stream/direct-upload`) needs
the actual CF API token and is out of scope until we have a paid CF account.
"""
import base64
import hashlib
import hmac
import time
from datetime import datetime
from typing import Any

from app.core.config import settings

PLAYBACK_TTL_S = 3600  # 1h, per CLAUDE.md §"How the three apps talk"


def _sign(uid: str, exp: int) -> str:
    """HMAC-SHA256({uid}:{exp}) base64url-encoded."""
    msg = f"{uid}:{exp}".encode()
    sig = hmac.new(settings.cf_stream_signing_key.encode(), msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def sign_playback_url(uid: str, ttl_seconds: int = PLAYBACK_TTL_S) -> str:
    """Build a signed manifest URL for the given video uid. Caller decides
    whether to embed this in an API response (mobile uses it directly)."""
    exp = int(time.time()) + ttl_seconds
    signature = _sign(uid, exp)
    return (
        f"https://customer-{settings.cf_account_id}.cloudflarestream.com/"
        f"{uid}/manifest/video.m3u8?exp={exp}&signature={signature}"
    )


async def mint_signed_playback_url(uid: str) -> str:
    """Async wrapper for router convenience. Same as sign_playback_url."""
    return sign_playback_url(uid)


async def mint_upload_url(episode_id: str) -> str:
    """Return a TUS direct-upload URL the creator's mobile client can PUT to.

    Cloudflare Stream's real implementation calls:
        POST https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/stream/direct-upload
        Authorization: Bearer {cf_api_token}
    and returns the uploadURL in the response. Until we have a real CF account,
    this is a placeholder — Phase 3 work.
    """
    return f"https://upload.cloudflarestream.com/{episode_id}?token=placeholder"


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Cloudflare signs webhook bodies with HMAC-SHA256 using the same
    cf_stream_signing_key. Header convention: `Webhook-Signature: <hex digest>`.
    Returns True iff the signature matches AND a signing key is configured.
    """
    if not settings.cf_stream_signing_key or not signature:
        return False
    expected = hmac.new(
        settings.cf_stream_signing_key.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)