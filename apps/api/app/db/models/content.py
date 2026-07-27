from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Series(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    synopsis: Mapped[str] = mapped_column(Text, nullable=False)
    cover_url: Mapped[str] = mapped_column(Text, nullable=False)
    backdrop_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    source: Mapped[str] = mapped_column(Enum("original", "tmdb", "creator", name="series_source"), nullable=False, default="original")
    creator_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    copyright_owner: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_vip_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    free_episodes: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    moderation_status: Mapped[str] = mapped_column(Enum("draft", "pending", "approved", "rejected", name="moderation_status"), nullable=False, default="draft")
    allowed_countries: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    tmdb_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_episodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    episodes: Mapped[list["Episode"]] = relationship(back_populates="series", cascade="all, delete-orphan")

    @property
    def tags_list(self) -> list[str]:
        import json
        try:
            return json.loads(self.tags)
        except Exception:
            return []

    @tags_list.setter
    def tags_list(self, value: list[str]) -> None:
        import json
        self.tags = json.dumps(value or [])


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    series_id: Mapped[str] = mapped_column(ForeignKey("series.id"), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_s: Mapped[int] = mapped_column(Integer, nullable=False)
    video_uid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    required_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ad_preroll: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ad_midroll_at_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    series: Mapped["Series"] = relationship(back_populates="episodes")