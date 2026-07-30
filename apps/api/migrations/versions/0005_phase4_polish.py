"""Phase 4 polish — pg_trgm index for search + push_tokens table

Revision ID: 0005_phase4_polish
Revises: 0004_phase3_monetization
Create Date: 2026-07-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision = "0005_phase4_polish"
down_revision: Union[str, None] = "0004_phase3_monetization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index("idx_series_title_trgm", "series", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"})
    op.create_index("idx_series_synopsis_trgm", "series", ["synopsis"], postgresql_using="gin", postgresql_ops={"synopsis": "gin_trgm_ops"})
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.UUID, nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_push_tokens_user", "push_tokens", ["user_id"])
    op.create_index("idx_push_tokens_token", "push_tokens", ["token"])


def downgrade() -> None:
    op.drop_index("idx_push_tokens_token", table_name="push_tokens")
    op.drop_index("idx_push_tokens_user", table_name="push_tokens")
    op.drop_table("push_tokens")
    op.drop_index("idx_series_title_trgm", table_name="series")
    op.drop_index("idx_series_synopsis_trgm", table_name="series")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
