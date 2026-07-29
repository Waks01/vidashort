from app.core.pydantic_base import BaseSchema


class UserResponse(BaseSchema):
    id: str
    email: str
    name: str
    role: str
    avatar_url: str | None = None
    genres: list[str]
    language: str
    age_confirmed: bool
    onboarded: bool
    created_at: str


class WalletResponse(BaseSchema):
    coins: int
    vip: dict


class AdCapResponse(BaseSchema):
    used: int
    limit: int
    remaining: int
    resets_at: str


class StreakResponse(BaseSchema):
    day: int
    last_claimed_on: str | None = None


class MeResponse(BaseSchema):
    user: UserResponse
    wallet: WalletResponse
    ad_cap: AdCapResponse
    streak: StreakResponse


class UpdateMeRequest(BaseSchema):
    name: str | None = None
    avatar_url: str | None = None
    genres: list[str] | None = None
    language: str | None = None


class AgeConfirmRequest(BaseSchema):
    confirmed: bool