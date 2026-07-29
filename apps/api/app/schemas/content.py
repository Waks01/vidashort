from app.core.pydantic_base import BaseSchema


class SeriesItem(BaseSchema):
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


class EpisodeMeta(BaseSchema):
    number: int
    title: str
    synopsis: str | None = None
    duration_s: int
    required_coins: int
    is_free: bool
    thumbnail_url: str | None = None


class SeriesDetail(BaseSchema):
    series: SeriesItem
    episodes: list[EpisodeMeta]


class SeriesListResponse(BaseSchema):
    items: list[SeriesItem]
    next_cursor: str | None = None


class StreamResponse(BaseSchema):
    episode_id: str
    playback_url: str
    expires_at: str
    captions_url: str | None = None
    preroll_ad: dict | None = None
    midroll_at_s: int | None = None
    poster_url: str | None = None


class PaywallDecisionSchema(BaseSchema):
    path: str
    cost_coins: int
    reward_coins: int
    remaining_ads: int
    label: str


class EntitlementError(BaseSchema):
    error: str
    message: str
    details: dict | None = None


class FavoriteResponse(BaseSchema):
    ok: bool = True


class FeaturedItem(BaseSchema):
    episode_id: str
    series_id: str
    slot: str
    order: int
    sponsor: str | None = None


class FeaturedResponse(BaseSchema):
    items: list[FeaturedItem]