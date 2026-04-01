from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.invitations.model import Invitation
    from app.teams.model import Team
    from app.users.model import User


class Project(Base):

    __table_args__ = (
        UniqueConstraint("creator_uuid", "title", name="uq_projects_creator_title"),
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())
    creator_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("users.uuid", ondelete="CASCADE"),
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

    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_projects",
        foreign_keys=[creator_uuid],
    )

    teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def teams_count(self) -> int:

        return len(self.teams)
