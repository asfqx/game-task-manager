from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.invitations.model import Invitation
    from app.users.model import User
    from app.projects.model import Project
    from app.lvls.model import Lvl


class Team(Base):

    __table_args__ = (
        UniqueConstraint("project_uuid", "name", name="uq_teams_project_name"),
    )

    project_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("projects.uuid", ondelete="CASCADE"),
    )

    created_by_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    lead_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text())

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="teams",
    )

    created_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_teams",
        foreign_keys=[created_by_uuid],
    )

    lead: Mapped["User | None"] = relationship(
        "User",
        back_populates="led_teams",
        foreign_keys=[lead_uuid],
    )

    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def members_count(self) -> int:

        return len({member.user_uuid for member in self.members})

    @property
    def lead_name(self) -> str | None:

        return self.lead.fio if self.lead is not None else None

    @property
    def project_title(self) -> str:

        return self.project.title


class TeamMember(Base):
    
    __table_args__ = (
        UniqueConstraint("team_uuid", "user_uuid", name="uq_team_members_team_user"),
    )

    team_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("teams.uuid", ondelete="CASCADE"),
    )

    user_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("users.uuid", ondelete="CASCADE"),
    )

    added_by_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    lvl_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("lvls.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    xp_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships",
        foreign_keys=[user_uuid],
    )

    added_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="added_team_memberships",
        foreign_keys=[added_by_uuid],
    )

    lvl: Mapped["Lvl | None"] = relationship(
        "Lvl",
        back_populates="team_members",
        foreign_keys=[lvl_uuid],
    )

    @property
    def is_team_lead(self) -> bool:

        return self.team.lead_uuid == self.user_uuid


from app.lvls.model import Lvl
from app.invitations.model import Invitation
