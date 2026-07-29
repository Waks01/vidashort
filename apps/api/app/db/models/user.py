from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum("viewer", "creator", "admin", name="user_role"), nullable=False, default="viewer")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    loyalty_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    genres: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    age_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    onboarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    banned_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def genres_list(self) -> list[str]:
        import json
        try:
            return json.loads(self.genres)
        except Exception:
            return []

    @genres_list.setter
    def genres_list(self, value: list[str]) -> None:
        import json
        self.genres = json.dumps(value or [])