from pydantic import BaseModel


class CreatorProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    handle: str
    bio: str | None = None
    niche: str | None = None
    avatar_url: str | None = None
    follower_count: int = 0
    total_views: int = 0
    payout_method: str | None = None
    payout_account: str | None = None
    payout_account_name: str | None = None
    verified: bool = False
    created_at: str


class CreatorProfileRequest(BaseModel):
    name: str | None = None
    bio: str | None = None
    niche: str | None = None
    payout_method: str | None = None
    payout_account: str | None = None


class CreatorSeriesItem(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    language: str
    total_episodes: int
    moderation_status: str
    is_published: bool
    total_views: int = 0
    total_unlocks: int = 0
    earnings_coins: int = 0
    earnings_naira: float = 0.0
    created_at: str


class CreatorSeriesResponse(BaseModel):
    items: list[CreatorSeriesItem]


class CreatorSeriesCreateRequest(BaseModel):
    title: str
    synopsis: str
    category: str
    language: str = "en"
    tags: list[str]
    total_episodes: int


class UploadUrlItem(BaseModel):
    episode_number: int
    video_upload_url: str | None = None
    cover_upload_url: str | None = None


class CreatorSeriesCreateResponse(BaseModel):
    series: CreatorSeriesItem
    upload_urls: list[UploadUrlItem]


class CreatorAnalyticsResponse(BaseModel):
    totals: dict
    daily: list[dict]
    by_series: list[dict]


class CreatorEarningsResponse(BaseModel):
    lifetime: dict
    pending: dict
    transactions: list[dict]


class PayoutRequest(BaseModel):
    amount_coins: int


class PayoutResponse(BaseModel):
    payout: dict


class PayoutItem(BaseModel):
    id: str
    amount_coins: int
    amount_naira: float
    status: str
    payout_method: str
    payout_account: str
    requested_at: str
    decided_at: str | None = None
    decided_by: str | None = None
    note: str | None = None


class PayoutListResponse(BaseModel):
    items: list[PayoutItem]