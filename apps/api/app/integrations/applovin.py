"""AppLovin MAX integration.

S2S reward callbacks: AppLovin hits our `/v1/webhooks/applovin` endpoint with
a reward event when the user completes a rewarded video. We verify the
signature, then call `app.services.ads.record_ad` to credit coins.

Signature scheme (AppLovin docs): HMAC-SHA256 of
    f"{event_id}|{user_id}|{ad_unit}|{currency}|{amount}|{timestamp}"
using the AppLovin S2S reward callback key. We compare hex digests in
constant time.

Conversion reporting: postbacks to AppLovin's `/conversion` endpoint for
attribution. Phase 3 work — the URL + body need the real event tokens.
"""
import hashlib
import hmac
from typing import Any


def verify_s2s_callback(
    *,
    event_id: str,
    user_id: str,
    ad_unit: str,
    currency: str,
    revenue: float,
    timestamp: int,
    signature: str,
    secret: str,
) -> bool:
    """Verify the AppLovin S2S reward callback signature. The mobile client
    receives the `?signature=...` param from AppLovin's SDK and forwards it
    to /v1/ads/record. We re-sign the same payload and compare.
    """
    if not secret or not signature:
        return False
    msg = f"{event_id}|{user_id}|{ad_unit}|{currency}|{revenue}|{timestamp}".encode()
    expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def report_conversion(event_name: str, user_id: str, revenue: float) -> None:
    """Postback to AppLovin's conversion endpoint for attribution.

    Real endpoint: POST https://postbacks-app.com/conversion
    Headers: Authorization: Bearer {applovin_api_key}
    Body: {"event": event_name, "user_id": user_id, "revenue": revenue}

    Phase 3 work — needs the real AppLovin API key + postback URL.
    """
    return None