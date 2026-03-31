from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.enum import TaskStatus

if TYPE_CHECKING:
    from app.teams.model import Team
    from app.users.model import User


class Task(Base):

    team_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("teams.uuid", ondelete="CASCADE"),
    )

    issuer_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    assignee_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text())

    review_comment: Mapped[str | None] = mapped_column(Text())

    xp_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus"),
        default=TaskStatus.CREATED,
    )

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    submitted_for_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    team: Mapped["Team"] = relationship("Team")

    issuer_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[issuer_user_uuid],
    )

    assignee_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assignee_user_uuid],
    )
