from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.enum import UserRole, UserStatus, Gender


class User(Base):
    
    email: Mapped[str] = mapped_column(String(255), unique=True)
    
    username: Mapped[str] = mapped_column(String(100))
    
    fio: Mapped[str] = mapped_column(String(50))
    
    role: Mapped[UserRole]
    
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    
    gender: Mapped[Gender | None] = mapped_column(String(255))
    
    telegram: Mapped[str | None] = mapped_column(String(255))
    
    phone_number: Mapped[str | None] = mapped_column(String(32))
    
    password_hash: Mapped[str] = mapped_column(String(255))
    
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="userstatus"),
        default=UserStatus.ACTIVE
    )
    
    email_confirmed: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.creator_uuid",
    )

    created_teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="created_by",
        foreign_keys="Team.created_by_uuid",
    )

    led_teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="lead",
        foreign_keys="Team.lead_uuid",
    )

    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        foreign_keys="TeamMember.user_uuid",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    added_team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="added_by",
        foreign_keys="TeamMember.added_by_uuid",
    )
