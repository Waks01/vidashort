from app.core.pydantic_base import BaseSchema


class AdCapResponse(BaseSchema):
    used: int
    limit: int
    remaining: int
    resets_at: str


class AdRecordRequest(BaseSchema):
    ad_id: str
    watched_s: int
    completed: bool


class AdRecordResponse(BaseSchema):
    ok: bool
    rewarded_coins: int
    new_balance: int
    remaining: int