from app.core.pydantic_base import BaseSchema


class DeviceRegisterRequest(BaseSchema):
    token: str
    platform: str


class DeviceResponse(BaseSchema):
    id: str
    platform: str
