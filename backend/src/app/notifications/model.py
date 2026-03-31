from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.users.model import User


class Notification(Base):

    content: Mapped[str] = mapped_column(Text())

    recipient_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=True,
    )

    sender_user_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    recipient_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[recipient_user_uuid],
    )

    sender_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[sender_user_uuid],
    )
