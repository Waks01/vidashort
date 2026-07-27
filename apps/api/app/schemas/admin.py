from pydantic import BaseModel


class AdminOverviewResponse(BaseModel):
    gmv_naira: float
    net_revenue_naira: float
    dau: int
    mau: int
    new_signups: int
    paying_users: int
    active_vip: int
    ad_cap_hits: int
    moderation_queue_size: int
    pending_payouts_naira: float
    top_series: list[dict]


class AdminModerationItem(BaseModel):
    id: str
    kind: str
    ref_id: str
    title: str | None = None
    submitted_by: str | None = None
    submitted_at: str | None = None
    reason: str
    preview: dict | None = None


class AdminModerationResponse(BaseModel):
    items: list[AdminModerationItem]
    next_cursor: str | None = None


class AdminModerationDecideRequest(BaseModel):
    decision: str
    note: str | None = None


class AdminUserUpdateRequest(BaseModel):
    role: str | None = None
    banned: bool | None = None
    ban_reason: str | None = None
    refund_coins: int | None = None


class AdminAdCampaignItem(BaseModel):
    id: str
    name: str
    network: str
    ad_unit_id: str
    type: str
    status: str
    fill_rate: float
    ecpm_naira: float
    daily_impressions: int
    daily_completions: int
    updated_at: str


class AdminFinanceResponse(BaseModel):
    net_revenue_naira: float
    gross_coin_sales_naira: float
    creator_liability_naira: float
    platform_net_naira: float
    ledger: list[dict]


class AdminPayoutDecideRequest(BaseModel):
    decision: str
    note: str | None = None