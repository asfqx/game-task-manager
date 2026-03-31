from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lvls.model import Lvl


class LvlRepository:

    @staticmethod
    async def get(
        lvl_uuid: UUID,
        session: AsyncSession,
    ) -> Lvl | None:

        stmt = select(Lvl).where(Lvl.uuid == lvl_uuid)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        session: AsyncSession,
    ) -> Sequence[Lvl]:

        stmt = select(Lvl).order_by(Lvl.required_xp, Lvl.value)
        result = await session.execute(stmt)

        return result.scalars().all()

    @staticmethod
    async def get_by_value(
        value: str,
        session: AsyncSession,
    ) -> Lvl | None:

        stmt = select(Lvl).where(Lvl.value == value)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_required_xp(
        required_xp: int,
        session: AsyncSession,
    ) -> Lvl | None:

        stmt = select(Lvl).where(Lvl.required_xp == required_xp)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_entry_level(
        session: AsyncSession,
    ) -> Lvl | None:

        stmt = (
            select(Lvl)
            .order_by(Lvl.required_xp, Lvl.value)
            .limit(1)
        )
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_for_xp(
        xp_amount: int,
        session: AsyncSession,
    ) -> Lvl | None:

        stmt = (
            select(Lvl)
            .where(Lvl.required_xp <= xp_amount)
            .order_by(desc(Lvl.required_xp), Lvl.value)
            .limit(1)
        )
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        lvl_obj: Lvl,
        session: AsyncSession,
    ) -> Lvl:

        session.add(lvl_obj)
        await session.commit()
        await session.refresh(lvl_obj)

        return lvl_obj

    @staticmethod
    async def update(
        lvl_obj: Lvl,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> Lvl:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(lvl_obj, field):
                setattr(lvl_obj, field, value)

        await session.commit()
        await session.refresh(lvl_obj)

        return lvl_obj
