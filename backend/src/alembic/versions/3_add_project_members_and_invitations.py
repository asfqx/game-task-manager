"""add team invitations

Revision ID: 8d7e2e3f4a10
Revises: 3d6163917539
Create Date: 2026-03-31 19:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8d7e2e3f4a10"
down_revision: Union[str, Sequence[str], None] = "3d6163917539"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

invitation_status_enum = postgresql.ENUM(
    "WAITING",
    "ACCEPTED",
    "REJECTED",
    name="invitationstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    invitation_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "invitations",
        sa.Column("team_uuid", sa.Uuid(), nullable=False),
        sa.Column("project_uuid", sa.Uuid(), nullable=False),
        sa.Column("sender_user_uuid", sa.Uuid(), nullable=True),
        sa.Column("recipient_user_uuid", sa.Uuid(), nullable=False),
        sa.Column("recipient_login", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            invitation_status_enum,
            server_default=sa.text("'WAITING'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_uuid"], ["projects.uuid"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_uuid"], ["teams.uuid"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_user_uuid"], ["users.uuid"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_uuid"], ["users.uuid"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint(
            "team_uuid",
            "recipient_user_uuid",
            "status",
            name="uq_invitations_team_recipient_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("invitations")

    bind = op.get_bind()
    invitation_status_enum.drop(bind, checkfirst=True)