"""Phase 3 monetization tables

Revision ID: 0004_phase3_monetization
Revises: 0003_users_email_verified
Create Date: 2026-07-29
"""
from typing import Sequence, Union
from alembic import op


revision = "0004_phase3_monetization"
down_revision: Union[str, None] = "0003_users_email_verified"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables already created in 0001_initial; this revision documents the
    # Phase 3 delivery checkpoint.
    pass


def downgrade() -> None:
    pass
