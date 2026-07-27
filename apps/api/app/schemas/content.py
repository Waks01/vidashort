from pydantic import BaseModel


class SeriesItem(BaseModel):
    id: str
    slug: str
    title: str
    synopsis: str
    cover_url: str
    backdrop_url: str | None = None
    category: str
    language: str
    source: str
    creator_id: str | None = None
    tags: list[str]
    total_episodes: int
    free_episodes: int
    is_vip_only: bool
    rating: float
    created_at: str


class EpisodeMeta(BaseModel):
    number: int
    title: str
    synopsis: str | None = None
    duration_s: int
    required_coins: int
    is_free: bool
    thumbnail_url: str | None = None


class SeriesDetail(BaseModel):
    series: SeriesItem
    episodes: list[EpisodeMeta]


class SeriesListResponse(BaseModel):
    items: list[SeriesItem]
    next_cursor: str | None = None


class StreamResponse(BaseModel):
    episode_id: str
    playback_url: str
    expires_at: str
    captions_url: str | None = None
    preroll_ad: dict | None = None
    midroll_at_s: int | None = None
    poster_url: str


class PaywallDecisionSchema(BaseModel):
    path: str
    cost_coins: int
    reward_coins: int
    remaining_ads: int
    label: str


class EntitlementError(BaseModel):
    error: str
    message: str
    details: dict | None = None


class FavoriteResponse(BaseModel):
    ok: bool = True


class FeaturedItem(BaseModel):
    episode_id: str
    series_id: str
    slot: str
    order: int
    sponsor: str | None = None


class FeaturedResponse(BaseModel):
    items: list[FeaturedItem]