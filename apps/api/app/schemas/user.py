from pydantic import BaseModel


class UserResponse(BaseModel):
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


class WalletResponse(BaseModel):
    coins: int
    vip: dict


class AdCapResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    resets_at: str


class StreakResponse(BaseModel):
    day: int
    last_claimed_on: str | None = None


class MeResponse(BaseModel):
    user: UserResponse
    wallet: WalletResponse
    ad_cap: AdCapResponse
    streak: StreakResponse


class UpdateMeRequest(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    genres: list[str] | None = None
    language: str | None = None


class AgeConfirmRequest(BaseModel):
    confirmed: bool