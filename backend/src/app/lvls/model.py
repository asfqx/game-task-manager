from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.teams.model import TeamMember


class Lvl(Base):

    __table_args__ = (
        UniqueConstraint("value", name="uq_lvls_value"),
        UniqueConstraint("required_xp", name="uq_lvls_required_xp"),
    )

    value: Mapped[str] = mapped_column(String(255))

    required_xp: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    team_members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="lvl",
    )
