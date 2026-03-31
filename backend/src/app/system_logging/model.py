from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.system_logging.type import UserActionLogDetailsPayload


class XpAccrualLog(Base):

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    xp_amount: Mapped[int] = mapped_column(Integer)

    recipient_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    issuer_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    task_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("tasks.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    recipient_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[recipient_user_uuid],
    )

    issuer_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[issuer_user_uuid],
    )

    task: Mapped["Task | None"] = relationship("Task")


class UserActionLog(Base):

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    actor_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(String(100))

    entity_type: Mapped[str | None] = mapped_column(String(100))

    entity_uuid: Mapped[UUID | None]

    details: Mapped[UserActionLogDetailsPayload | None] = mapped_column(JSON, nullable=True)

    actor_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[actor_user_uuid],
    )
