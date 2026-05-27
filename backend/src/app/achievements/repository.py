from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.achievements.model import UserAchievement


class UserAchievementRepository:

    @staticmethod
    async def get_by_user(
        user_uuid: UUID,
        session: AsyncSession,
    ) -> Sequence[UserAchievement]:

        stmt = (
            select(UserAchievement)
            .where(UserAchievement.user_uuid == user_uuid)
            .order_by(UserAchievement.unlocked_at)
        )
        result = await session.execute(stmt)

        return result.scalars().all()

    @staticmethod
    async def create(
        achievement: UserAchievement,
        session: AsyncSession,
    ) -> UserAchievement:

        session.add(achievement)
        await session.flush()

        return achievement
