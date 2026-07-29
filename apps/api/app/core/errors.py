class AppError(Exception):
    status_code: int = 400
    code: str = "bad_request"
    detail: str = "Bad request"

    def __init__(self, *, status_code: int | None = None, code: str | None = None, detail: str | None = None):
        self.status_code = status_code if status_code is not None else type(self).status_code
        self.code = code if code is not None else type(self).code
        self.detail = detail if detail is not None else type(self).detail
        super().__init__(self.detail)


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
