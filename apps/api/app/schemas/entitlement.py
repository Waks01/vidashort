from app.core.pydantic_base import BaseSchema


class CheckRequest(BaseSchema):
    episode_id: str


class CheckResponse(BaseSchema):
    allowed: bool
    source: str | None = None
    paywall: dict | None = None


class UnlockRequest(BaseSchema):
    episode_id: str
    source: str


class UnlockResponse(BaseSchema):
    ok: bool
    source: str
    coins_after: int | None = None
    creator_credited_coins: int | None = None
    playback_url: str | None = None