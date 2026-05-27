"""add user achievements

Revision ID: 4f6a6e2c9b31
Revises: 8d7e2e3f4a10
Create Date: 2026-05-27 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f6a6e2c9b31"
down_revision: Union[str, Sequence[str], None] = "8d7e2e3f4a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_achievements",
        sa.Column("user_uuid", sa.Uuid(), nullable=False),
        sa.Column("achievement_key", sa.String(length=100), nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_uuid"], ["users.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint("user_uuid", "achievement_key", name="uq_user_achievements_user_key"),
    )


def downgrade() -> None:
    op.drop_table("user_achievements")
