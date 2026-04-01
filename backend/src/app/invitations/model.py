from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.enum import InvitationStatus

if TYPE_CHECKING:
    from app.projects.model import Project
    from app.teams.model import Team
    from app.users.model import User


class Invitation(Base):

    __table_args__ = (
        UniqueConstraint("team_uuid", "recipient_user_uuid", "status", name="uq_invitations_team_recipient_status"),
    )

    team_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("teams.uuid", ondelete="CASCADE"),
    )

    project_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("projects.uuid", ondelete="CASCADE"),
    )

    sender_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    recipient_user_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("users.uuid", ondelete="CASCADE"),
    )

    recipient_login: Mapped[str] = mapped_column(String(255))

    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, name="invitationstatus"),
        default=InvitationStatus.WAITING,
        server_default=InvitationStatus.WAITING.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="invitations",
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="invitations",
    )

    sender_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="sent_invitations",
        foreign_keys=[sender_user_uuid],
    )

    recipient_user: Mapped["User"] = relationship(
        "User",
        back_populates="received_invitations",
        foreign_keys=[recipient_user_uuid],
    )
