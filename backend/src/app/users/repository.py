from collections.abc import Callable, Sequence
import datetime as dt
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.filter import UserFilterQueryParams
from app.users.model import User
from app.users.type import UserFilterPayload
from app.enum import UserStatus


class UserRepository:

    @staticmethod
    def _build_conditions(filters: UserFilterPayload) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "cursor": lambda v: User.uuid > v,
            "username": lambda v: User.username.ilike(f"%{v}%"),
            "email": lambda v: User.email.ilike(f"%{v}%"),
            "fio": lambda v: User.fio.ilike(f"%{v}%"),
            "role": lambda v: User.role == v,
            "gender": lambda v: User.gender == v,
        }

        return [
            filter_mapping[k](v)
            for k, v in filters.items()
            if k in filter_mapping and v is not None
        ]

    @staticmethod
    async def set_last_login(
        user_obj: User,
        session: AsyncSession,
    ) -> None:

        stmt = text("UPDATE users SET last_login_at = :last_login_at WHERE uuid = :uuid")

        await session.execute(
            stmt,
            {
                "last_login_at": dt.datetime.now(dt.UTC),
                "uuid": str(user_obj.uuid),
            },
        )
        await session.commit()
        await session.refresh(user_obj)

    @staticmethod
    async def update_password(
        user_obj: User,
        new_password: str,
        session: AsyncSession,
    ) -> None:

        user_obj.password_hash = new_password

        await session.commit()

    @staticmethod
    async def update_email_confirm(
        user_obj: User,
        session: AsyncSession,
    ) -> None:

        user_obj.email_confirmed = True

        await session.commit()

    @staticmethod
    async def get(
        user_uuid: UUID,
        session: AsyncSession,
    ) -> User | None:

        stmt = select(User).where(User.uuid == user_uuid)

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        filters: UserFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[User]:

        stmt_filters = filters.model_dump(exclude_none=True)
        conditions = UserRepository._build_conditions(stmt_filters)

        stmt = (
            select(User)
            .where(*conditions)
            .order_by(User.uuid)
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().all()

    @staticmethod
    async def get_without_email(session: AsyncSession) -> Sequence[User]:

        stmt = (
            select(User)
            .where(User.email_confirmed.is_(False))
        )

        result = await session.execute(stmt)

        return result.scalars().all()

    @staticmethod
    async def delete(
        user: User,
        session: AsyncSession,
    ) -> User:

        await session.delete(user)
        await session.commit()

        return user

    @staticmethod
    async def get_by_login(
        login: str,
        session: AsyncSession,
    ) -> User | None:

        stmt = select(User).where(
            or_(
                User.email == login.lower(),
                User.username == login,
            )
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        user_obj: User,
        session: AsyncSession,
    ) -> User:

        session.add(user_obj)

        await session.commit()
        await session.refresh(user_obj)

        return user_obj

    @staticmethod
    async def update(
        user_obj: User,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> User:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(user_obj, field):
                setattr(user_obj, field, value)

        await session.commit()
        await session.refresh(user_obj)

        return user_obj
    
    @staticmethod
    async def ban(
        user_obj: User,
        session: AsyncSession,
    ) -> None:

        user_obj.status = UserStatus.BANNED

        await session.commit()
        await session.refresh(user_obj)

    @staticmethod
    async def unban(
        user_obj: User,
        session: AsyncSession,
    ) -> None:

        user_obj.status = UserStatus.ACTIVE

        await session.commit()
        await session.refresh(user_obj)

