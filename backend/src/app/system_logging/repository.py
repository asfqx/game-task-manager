from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.system_logging.filter import (
    UserActionLogFilterQueryParams,
    XpAccrualLogFilterQueryParams,
)
from app.system_logging.model import UserActionLog, XpAccrualLog
from app.system_logging.type import UserActionLogFilterPayload, XpAccrualLogFilterPayload
from app.tasks.model import Task
from app.teams.model import Team


XP_LOG_LOAD_OPTIONS = (
    selectinload(XpAccrualLog.recipient_user),
    selectinload(XpAccrualLog.issuer_user),
    selectinload(XpAccrualLog.task).selectinload(Task.team).selectinload(Team.project),
)

USER_ACTION_LOG_LOAD_OPTIONS = (
    selectinload(UserActionLog.actor_user),
)


class XpAccrualLogRepository:

    @staticmethod
    def _build_conditions(filters: XpAccrualLogFilterPayload) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "cursor": lambda value: XpAccrualLog.uuid > value,
            "recipient_user_uuid": lambda value: XpAccrualLog.recipient_user_uuid == value,
            "issuer_user_uuid": lambda value: XpAccrualLog.issuer_user_uuid == value,
            "task_uuid": lambda value: XpAccrualLog.task_uuid == value,
            "team_uuid": lambda value: Task.team_uuid == value,
        }

        return [
            filter_mapping[key](value)
            for key, value in filters.items()
            if key in filter_mapping and value is not None
        ]

    @staticmethod
    async def create(
        log_obj: XpAccrualLog,
        session: AsyncSession,
    ) -> XpAccrualLog:

        session.add(log_obj)
        await session.flush()

        return log_obj

    @staticmethod
    async def update(
        log_obj: XpAccrualLog,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> XpAccrualLog:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(log_obj, field):
                setattr(log_obj, field, value)

        await session.commit()
        await session.refresh(log_obj)

        return log_obj

    @staticmethod
    async def get_by_task_uuid(
        task_uuid: UUID,
        session: AsyncSession,
    ) -> XpAccrualLog | None:

        stmt = (
            select(XpAccrualLog)
            .options(*XP_LOG_LOAD_OPTIONS)
            .where(XpAccrualLog.task_uuid == task_uuid)
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        filters: XpAccrualLogFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[XpAccrualLog]:

        conditions = XpAccrualLogRepository._build_conditions(filters.model_dump(exclude_none=True))

        stmt = (
            select(XpAccrualLog)
            .options(*XP_LOG_LOAD_OPTIONS)
            .outerjoin(Task, Task.uuid == XpAccrualLog.task_uuid)
            .where(*conditions)
            .order_by(XpAccrualLog.uuid)
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()


class UserActionLogRepository:

    @staticmethod
    def _build_conditions(filters: UserActionLogFilterPayload) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "cursor": lambda value: UserActionLog.uuid > value,
            "actor_user_uuid": lambda value: UserActionLog.actor_user_uuid == value,
            "action": lambda value: UserActionLog.action == value,
            "entity_type": lambda value: UserActionLog.entity_type == value,
            "entity_uuid": lambda value: UserActionLog.entity_uuid == value,
        }

        return [
            filter_mapping[key](value)
            for key, value in filters.items()
            if key in filter_mapping and value is not None
        ]

    @staticmethod
    async def create(
        log_obj: UserActionLog,
        session: AsyncSession,
    ) -> UserActionLog:

        session.add(log_obj)
        await session.flush()

        return log_obj

    @staticmethod
    async def update(
        log_obj: UserActionLog,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> UserActionLog:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(log_obj, field):
                setattr(log_obj, field, value)

        await session.commit()
        await session.refresh(log_obj)

        return log_obj

    @staticmethod
    async def get_all(
        filters: UserActionLogFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[UserActionLog]:

        conditions = UserActionLogRepository._build_conditions(filters.model_dump(exclude_none=True))

        stmt = (
            select(UserActionLog)
            .options(*USER_ACTION_LOG_LOAD_OPTIONS)
            .where(*conditions)
            .order_by(UserActionLog.uuid)
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()
