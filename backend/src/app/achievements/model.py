from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.core import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.users.model import User


class UserAchievement(Base):

    __table_args__ = (
        UniqueConstraint("user_uuid", "achievement_key", name="uq_user_achievements_user_key"),
    )

    user_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("users.uuid", ondelete="CASCADE"),
    )

    achievement_key: Mapped[str] = mapped_column(String(100))

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship("User")


from app.users.model import User
