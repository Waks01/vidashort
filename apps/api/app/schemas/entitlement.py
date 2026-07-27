from pydantic import BaseModel


class CheckRequest(BaseModel):
    episode_id: str


class CheckResponse(BaseModel):
    allowed: bool
    source: str | None = None


class UnlockRequest(BaseModel):
    episode_id: str
    source: str


class UnlockResponse(BaseModel):
    ok: bool
    source: str
    coins_after: int | None = None
    creator_credited_coins: int | None = None
    playback_url: str | None = None