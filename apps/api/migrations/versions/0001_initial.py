"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, CITEXT, JSON
from sqlalchemy import text


revision = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    op.create_table(
        "users",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", CITEXT, unique=True, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("role", sa.Enum("viewer", "creator", "admin", name="user_role"), server_default="viewer", nullable=False),
        sa.Column("avatar_url", sa.String(512)),
        sa.Column("coins", sa.Integer, server_default="0", nullable=False),
        sa.Column("loyalty_coins", sa.Integer, server_default="0", nullable=False),
        sa.Column("genres", ARRAY(sa.String), server_default="{}", nullable=False),
        sa.Column("language", sa.String(10), server_default="en", nullable=False),
        sa.Column("age_confirmed", sa.Boolean, server_default="false", nullable=False),
        sa.Column("onboarded", sa.Boolean, server_default="false", nullable=False),
        sa.Column("banned_at", sa.DateTime(timezone=True)),
        sa.Column("ban_reason", sa.Text),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_users_role", "users", ["role"], postgresql_where=sa.text("role != 'viewer'"))
    op.create_index("idx_users_deleted_at", "users", ["deleted_at"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_table(
        "user_identities",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("provider", sa.Enum("email", "apple", "google", name="identity_provider"), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_user_identity_provider"),
    )
    op.create_index("idx_user_identities_user_id", "user_identities", ["user_id"])
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.Text),
        sa.Column("ip", sa.String(45)),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table(
        "password_resets",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "series",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("synopsis", sa.Text, nullable=False),
        sa.Column("cover_url", sa.Text, nullable=False),
        sa.Column("backdrop_url", sa.Text),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("language", sa.String(10), server_default="en", nullable=False),
        sa.Column("source", sa.Enum("original", "tmdb", "creator", name="series_source"), server_default="original", nullable=False),
        sa.Column("creator_id", UUID),
        sa.Column("copyright_owner", sa.Text),
        sa.Column("is_published", sa.Boolean, server_default="false", nullable=False),
        sa.Column("is_vip_only", sa.Boolean, server_default="false", nullable=False),
        sa.Column("free_episodes", sa.Integer, server_default="3", nullable=False),
        sa.Column("moderation_status", sa.Enum("draft", "pending", "approved", "rejected", name="moderation_status"), server_default="draft", nullable=False),
        sa.Column("allowed_countries", ARRAY(sa.String)),
        sa.Column("tags", ARRAY(sa.String), server_default="{}", nullable=False),
        sa.Column("tmdb_id", sa.String(50)),
        sa.Column("total_episodes", sa.Integer, server_default="0", nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_series_published", "series", ["is_published", "total_episodes"], postgresql_where=sa.text("is_published = true"))
    op.create_index("idx_series_category", "series", ["category"], postgresql_where=sa.text("is_published = true"))
    op.create_index("idx_series_creator", "series", ["creator_id"])
    op.create_index("idx_series_pending", "series", ["moderation_status"], postgresql_where=sa.text("moderation_status = 'pending'"))
    op.create_table(
        "episodes",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("series_id", UUID, nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("synopsis", sa.Text),
        sa.Column("duration_s", sa.Integer, nullable=False),
        sa.Column("video_uid", sa.String(255)),
        sa.Column("video_ready", sa.Boolean, server_default="false", nullable=False),
        sa.Column("required_coins", sa.Integer, server_default="25", nullable=False),
        sa.Column("is_free", sa.Boolean, server_default="false", nullable=False),
        sa.Column("ad_preroll", sa.Boolean, server_default="true", nullable=False),
        sa.Column("ad_midroll_at_s", sa.Integer),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("series_id", "number", name="uq_episode_series_number"),
    )
    op.create_index("idx_episodes_series", "episodes", ["series_id", "number"])
    op.create_table(
        "watch_history",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("episode_id", UUID, nullable=False),
        sa.Column("position_s", sa.Integer, server_default="0", nullable=False),
        sa.Column("completed", sa.Boolean, server_default="false", nullable=False),
        sa.Column("unlocked_via_coins", sa.Boolean, server_default="false", nullable=False),
        sa.Column("unlocked_via_ad", sa.Boolean, server_default="false", nullable=False),
        sa.Column("unlocked_via_vip", sa.Boolean, server_default="false", nullable=False),
        sa.Column("watched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_watch_history_resume", "watch_history", ["user_id", "episode_id", "watched_at"])
    op.create_index("idx_watch_history_user", "watch_history", ["user_id", "watched_at"])
    op.create_table(
        "favorites",
        sa.Column("user_id", UUID, primary_key=True),
        sa.Column("series_id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "comments",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("episode_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("parent_id", UUID),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("likes", sa.Integer, server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_comments_episode", "comments", ["episode_id", "created_at"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_comments_user", "comments", ["user_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_table(
        "coin_txn",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("delta", sa.Integer, nullable=False),
        sa.Column("reason", sa.Enum("purchase", "rewarded_ad", "unlock", "refund", "daily_reward", "admin_grant", "admin_refund", "restore", name="coin_txn_reason"), nullable=False),
        sa.Column("ref_id", UUID),
        sa.Column("balance_after", sa.Integer, nullable=False),
        sa.Column("idempotency_key", sa.String(255), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_coin_txn_user", "coin_txn", ["user_id", "created_at"])
    op.create_table(
        "creator_earnings",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("creator_id", UUID, nullable=False),
        sa.Column("episode_id", UUID, nullable=False),
        sa.Column("gross_coins", sa.Integer, nullable=False),
        sa.Column("creator_coins", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_creator_earnings_creator", "creator_earnings", ["creator_id", "created_at"])
    op.create_table(
        "payout_requests",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("creator_id", UUID, nullable=False),
        sa.Column("amount_coins", sa.Integer, nullable=False),
        sa.Column("amount_naira", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "paid", "cancelled", name="payout_status"), server_default="pending", nullable=False),
        sa.Column("payout_method", sa.Enum("OPay", "PalmPay", "Moniepoint", "Bank", name="payout_method"), nullable=False),
        sa.Column("payout_account", sa.Text, nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", UUID),
        sa.Column("note", sa.Text),
    )
    op.create_index("idx_payout_requests_creator", "payout_requests", ["creator_id", "requested_at"])
    op.create_index("idx_payout_requests_status", "payout_requests", ["status", "requested_at"])
    op.create_table(
        "ad_impressions",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("ad_id", sa.String(255), nullable=False),
        sa.Column("ad_network", sa.String(50), server_default="appLovin", nullable=False),
        sa.Column("ad_type", sa.Enum("rewarded", "interstitial", name="ad_type"), nullable=False),
        sa.Column("watched_s", sa.Integer, nullable=False),
        sa.Column("completed", sa.Boolean, server_default="false", nullable=False),
        sa.Column("rewarded_coins", sa.Integer, server_default="0", nullable=False),
        sa.Column("country", sa.String(2)),
        sa.Column("app_version", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "ad_id", name="uq_ad_impression_user_ad"),
    )
    op.create_index("idx_ad_impressions_user_daily", "ad_impressions", ["user_id", sa.text("((created_at AT TIME ZONE 'UTC')::date)")])
    op.create_index("idx_ad_impressions_type", "ad_impressions", ["ad_type", "created_at"])
    op.create_table(
        "vip_entitlements",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("source", sa.Enum("apple", "google", "revenuecat", "manual", name="vip_source"), nullable=False),
        sa.Column("product_id", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_renew", sa.Boolean, server_default="true", nullable=False),
        sa.Column("original_txn_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_vip_entitlements_user_active", "vip_entitlements", ["user_id", "expires_at"])
    op.create_table(
        "moderation_items",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("kind", sa.Enum("series", "comment", "account", name="moderation_kind"), nullable=False),
        sa.Column("ref_id", UUID, nullable=False),
        sa.Column("submitter_id", UUID),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="moderation_item_status"), server_default="pending", nullable=False),
        sa.Column("auto_flagged", sa.Boolean, server_default="false", nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", UUID),
        sa.Column("note", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_moderation_pending", "moderation_items", ["kind", "status", "created_at"], postgresql_where=sa.text("status = 'pending'"))
    op.create_table(
        "audit_log",
        sa.Column("id", UUID, server_default=text("gen_random_uuid()"), primary_key=True),
        sa.Column("actor_id", UUID, nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("target_kind", sa.String(100), nullable=False),
        sa.Column("target_id", UUID, nullable=False),
        sa.Column("before", JSON),
        sa.Column("after", JSON),
        sa.Column("ip", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_audit_log_actor", "audit_log", ["actor_id", "created_at"])
    op.create_index("idx_audit_log_target", "audit_log", ["target_kind", "target_id", "created_at"])
    op.create_foreign_key("fk_user_identities_user_id", "user_identities", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_refresh_tokens_user_id", "refresh_tokens", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_password_resets_user_id", "password_resets", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_series_creator_id", "series", "users", ["creator_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_episodes_series_id", "episodes", "series", ["series_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_watch_history_user_id", "watch_history", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_watch_history_episode_id", "watch_history", "episodes", ["episode_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_comments_episode_id", "comments", "episodes", ["episode_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_comments_user_id", "comments", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_comments_parent_id", "comments", "comments", ["parent_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_coin_txn_user_id", "coin_txn", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_creator_earnings_creator_id", "creator_earnings", "users", ["creator_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_creator_earnings_episode_id", "creator_earnings", "episodes", ["episode_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_payout_requests_creator_id", "payout_requests", "users", ["creator_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_payout_requests_decided_by", "payout_requests", "users", ["decided_by"], ["id"])
    op.create_foreign_key("fk_ad_impressions_user_id", "ad_impressions", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_vip_entitlements_user_id", "vip_entitlements", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_moderation_items_submitter_id", "moderation_items", "users", ["submitter_id"], ["id"])
    op.create_foreign_key("fk_moderation_items_decided_by", "moderation_items", "users", ["decided_by"], ["id"])
    op.create_foreign_key("fk_audit_log_actor_id", "audit_log", "users", ["actor_id"], ["id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("moderation_items")
    op.drop_table("vip_entitlements")
    op.drop_table("ad_impressions")
    op.drop_table("payout_requests")
    op.drop_table("creator_earnings")
    op.drop_table("coin_txn")
    op.drop_table("comments")
    op.drop_table("favorites")
    op.drop_table("watch_history")
    op.drop_table("episodes")
    op.drop_table("series")
    op.drop_table("password_resets")
    op.drop_table("refresh_tokens")
    op.drop_table("user_identities")
    op.drop_table("users")
    op.execute(text("DROP TYPE IF EXISTS user_role"))
    op.execute(text("DROP TYPE IF EXISTS identity_provider"))
    op.execute(text("DROP TYPE IF EXISTS series_source"))
    op.execute(text("DROP TYPE IF EXISTS moderation_status"))
    op.execute(text("DROP TYPE IF EXISTS coin_txn_reason"))
    op.execute(text("DROP TYPE IF EXISTS payout_status"))
    op.execute(text("DROP TYPE IF EXISTS payout_method"))
    op.execute(text("DROP TYPE IF EXISTS ad_type"))
    op.execute(text("DROP TYPE IF EXISTS vip_source"))
    op.execute(text("DROP TYPE IF EXISTS moderation_kind"))
    op.execute(text("DROP TYPE IF EXISTS moderation_item_status"))