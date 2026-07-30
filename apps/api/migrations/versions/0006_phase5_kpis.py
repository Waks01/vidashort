"""Create daily_kpis materialized view for admin finance dashboard."""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006_phase5_kpis"
down_revision: str = "0005_phase4_polish"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_kpis AS
        SELECT
            date_trunc('day', t.created_at) AS day,
            count(*) FILTER (WHERE t.reason = 'purchase') AS purchase_count,
            sum(t.delta) FILTER (WHERE t.reason = 'purchase') AS gross_coins,
            sum(t.delta) FILTER (WHERE t.reason = 'purchase') / 10.0 AS gross_naira,
            coalesce(sum(e.creator_coins), 0) AS creator_liability_coins,
            coalesce(sum(e.creator_coins) / 10.0, 0) AS creator_liability_naira,
            sum(t.delta) FILTER (WHERE t.reason = 'purchase') / 10.0 - coalesce(sum(e.creator_coins) / 10.0, 0) AS platform_net_naira
        FROM coin_txn t
        LEFT JOIN creator_earnings e ON date_trunc('day', e.created_at) = date_trunc('day', t.created_at)
        GROUP BY day
        ORDER BY day DESC;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mv_daily_kpis_day ON mv_daily_kpis (day);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_mv_daily_kpis_day;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_kpis;")
