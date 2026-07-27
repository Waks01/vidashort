class AppError(Exception):
    status_code: int = 400
    code: str = "bad_request"
    detail: str = "Bad request"


class NotFound(AppError):
    status_code = 404
    code = "not_found"
    detail = "Resource not found"


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"
    detail = "Too many requests"


class PaywallRequired(AppError):
    status_code = 403
    code = "paywall_required"
    detail = "Payment required to access this content"


class InsufficientCoins(PaywallRequired):
    code = "insufficient_coins"
    detail = "Not enough coins"


class AdCapReached(PaywallRequired):
    code = "ad_cap_reached"
    detail = "Daily ad cap reached"


class VipRequired(PaywallRequired):
    code = "vip_required"
    detail = "VIP subscription required"
