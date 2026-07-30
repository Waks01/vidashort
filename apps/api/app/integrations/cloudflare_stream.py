import base64
import time

from app.core.config import settings
from jose import jwt

PLAYBACK_TTL_S = 3600  # 1h, per CLAUDE.md "How the three apps talk"


def _load_signing_key() -> tuple[str, str]:
    """Return (decoded_pem, key_id).

    CF_STREAM_SIGNING_KEY is stored as base64-encoded PEM in .env.
    CF_STREAM_KEY_ID is the `id` from the /stream/keys response.

    Falls back to empty string when the value is not a valid PEM, so
    sign_playback_url returns an unsigned URL instead of crashing.
    """
    key = settings.cf_stream_signing_key or ""
    key_id = settings.cf_stream_key_id or ""
    if not key:
        return "", key_id
    try:
        decoded = base64.b64decode(key, validate=True)
        text = decoded.decode("utf-8", errors="strict")
        if "-----BEGIN" not in text or "PRIVATE KEY" not in text:
            return "", key_id
        return text, key_id
    except Exception:
        return "", key_id


def sign_playback_url(uid: str, ttl_seconds: int = PLAYBACK_TTL_S) -> str:
    """Build a signed manifest URL for the given video uid. Caller decides
    whether to embed this in an API response (mobile uses it directly).

    The token is an RS256 JWT whose `sub` claim is the video uid and whose
    `exp` claim is the TTL-limited unix timestamp. Cloudflare verifies the
    token using the public half of the Stream signing key created in
    `/accounts/{id}/stream/keys`.

    As of 2026-07 Cloudflare expects the token in the path position:
        https://customer-{account_id}.cloudflarestream.com/{token}/manifest/video.m3u8
    """
    private_pem, key_id = _load_signing_key()
    if not private_pem:
        return (
            f"https://customer-{settings.cf_account_id}.cloudflarestream.com/"
            f"{uid}/manifest/video.m3u8"
        )
    exp = int(time.time()) + ttl_seconds
    headers = {"alg": "RS256"}
    if key_id:
        headers["kid"] = key_id
    token = jwt.encode({"sub": uid, "exp": exp}, private_pem, algorithm="RS256", headers=headers)
    return (
        f"https://customer-{settings.cf_account_id}.cloudflarestream.com/"
        f"{token}/manifest/video.m3u8"
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
    """Cloudflare signs webhook bodies with HMAC-SHA256 using the separate
    `settings.cf_webhook_secret`. Header convention: `Webhook-Signature`
    with `time=<ts>,sig1=<hex>`.
    Returns True iff the signature matches and a webhook secret is configured.
    """
    if not settings.cf_webhook_secret or not signature:
        return False
    import hashlib
    import hmac
    try:
        parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
        ts = parts.get("time") or parts.get("t")
        sig = parts.get("sig1") or parts.get("v1")
        if not ts or not sig:
            return False
        expected = hmac.new(
            f"{ts}.".encode() + body,
            settings.cf_webhook_secret.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False
