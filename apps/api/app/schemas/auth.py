from pydantic import EmailStr, Field

from app.core.pydantic_base import BaseSchema


class SignupRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    accepted_terms: bool = True


class SigninRequest(BaseSchema):
    email: EmailStr
    password: str


class RefreshRequest(BaseSchema):
    refresh_token: str


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseSchema):
    user: dict
    access_token: str
    refresh_token: str


class AppleAuthRequest(BaseSchema):
    identity_token: str
    name: str | None = None
    email: str | None = None


class GoogleAuthRequest(BaseSchema):
    id_token: str


class ForgotRequest(BaseSchema):
    email: EmailStr


class ResetRequest(BaseSchema):
    token: str
    new_password: str = Field(min_length=8)


class OtpRequest(BaseSchema):
    email: EmailStr


class OtpVerifyRequest(BaseSchema):
    email: EmailStr
    code: str = Field(min_length=4, max_length=10)


class SignupResponse(BaseSchema):
    """Returned by POST /v1/auth/signup. Tokens are NOT issued at signup —
    the client must POST to /v1/auth/otp/verify next with the code emailed to
    the user, which returns the full AuthResponse with access/refresh tokens."""

    ok: bool = True
    requires_verification: bool = True