"""Email service — thin Resend wrapper.

Why Resend:
- The `RESEND_API_KEY` and `RESEND_EMAIL_FROM` settings are already in
  `app/core/config.py` and `.env`. No new dependency is added; we POST to
  https://api.resend.com/emails with httpx (already a dep).

Why we no-op when the key is empty:
- Local dev and CI run without a real Resend account. Logging the OTP /
  reset link to stdout lets the developer copy-paste from the server log
  to complete the flow without configuring a transactional email provider.
  Production sets `RESEND_API_KEY` and gets real email delivery.

Failure mode:
- On any non-2xx from Resend we log and return False. The auth flow itself
  still succeeds — the user is created / reset row is written — because the
  contract is "best-effort send + always-ok response" (we don't want to
  tell an attacker "your target email isn't valid"). The user can hit
  "Resend code" if the email didn't arrive.
"""
import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def _dev_log(label: str, body: str) -> None:
    """Dev-mode stand-in: print the message to the server log so the developer
    can copy the OTP / reset link and proceed without a real email provider."""
    log.warning("DEV EMAIL — %s\n%s", label, body)


def _send_resend(subject: str, to: str, html: str, text: str) -> bool:
    """POST to Resend. Returns True on 2xx. Logs + returns False on failure.
    Never raises — the auth flow must not 500 just because email failed."""
    if not settings.resend_api_key:
        _dev_log(subject, f"to: {to}\n{text}")
        return True
    try:
        resp = httpx.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.resend_email_from or "noreply@vidashort.app",
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=10.0,
        )
        if resp.status_code >= 300:
            log.error("Resend send failed: %s %s", resp.status_code, resp.text)
            return False
        return True
    except Exception as exc:
        log.error("Resend send exception: %s", exc)
        return False


async def send_otp(email: str, code: str) -> bool:
    """Send the 6-digit signup-verification code."""
    subject = "Your vidashort verification code"
    text = (
        f"Your vidashort verification code is: {code}\n\n"
        f"This code expires in {settings.otp_ttl_seconds // 60} minutes.\n\n"
        "If you didn't request this, you can safely ignore this email.\n"
    )
    html = (
        f"<p>Your vidashort verification code is:</p>"
        f"<p style='font-size:28px;font-weight:700;letter-spacing:6px'>{code}</p>"
        f"<p>This code expires in {settings.otp_ttl_seconds // 60} minutes.</p>"
        f"<p style='color:#888'>If you didn't request this, you can safely ignore this email.</p>"
    )
    return _send_resend(subject, email, html, text)


async def send_password_reset(email: str, deep_link: str) -> bool:
    """Send the password-reset deep link."""
    subject = "Reset your vidashort password"
    text = (
        "Tap the link below to set a new vidashort password:\n\n"
        f"{deep_link}\n\n"
        "This link expires in 1 hour. If you didn't request this, you can safely ignore this email.\n"
    )
    html = (
        f"<p>Tap the button below to set a new vidashort password:</p>"
        f"<p><a href='{deep_link}' style='display:inline-block;background:#ff1f5a;"
        f"color:#fff;padding:14px 24px;border-radius:9999px;text-decoration:none;"
        f"font-weight:700'>Set new password</a></p>"
        f"<p style='color:#888'>Or paste this link into the app: {deep_link}</p>"
        f"<p style='color:#888'>This link expires in 1 hour. "
        f"If you didn't request this, you can safely ignore this email.</p>"
    )
    return _send_resend(subject, email, html, text)
