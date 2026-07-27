from pydantic import BaseModel


class AdCapResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    resets_at: str


class AdRecordRequest(BaseModel):
    ad_id: str
    watched_s: int
    completed: bool


class AdRecordResponse(BaseModel):
    ok: bool
    rewarded_coins: int
    new_balance: int
    remaining: int