import hashlib
import hmac
from typing import Any

from app.core.config import settings


def sign_playback_url(uid: str, ttl_seconds: int = 3600) -> str:
    return f"https://customer-{settings.cf_account_id}.cloudflarestream.com/{uid}/manifest/video.m3u8?signature=placeholder"


async def mint_signed_playback_url(uid: str) -> str:
    return sign_playback_url(uid)


async def mint_upload_url(episode_id: str) -> str:
    return f"https://upload.cloudflarestream.com/{episode_id}?token=placeholder"


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(settings.cf_stream_signing_key.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)