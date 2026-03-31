from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.notifications.filter import NotificationFilterQueryParams
from app.notifications.model import Notification


NOTIFICATION_LOAD_OPTIONS = (
    selectinload(Notification.recipient_user),
    selectinload(Notification.sender_user),
)


class NotificationRepository:

    @staticmethod
    def _build_conditions(filters: NotificationFilterQueryParams) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "sender_user_uuid": lambda value: Notification.sender_user_uuid == value,
        }

        return [
            filter_mapping[key](value)
            for key, value in filters.items()
            if key in filter_mapping and value is not None
        ]

    @staticmethod
    async def get(
        notification_uuid: UUID,
        session: AsyncSession,
    ) -> Notification | None:

        stmt = (
            select(Notification)
            .options(*NOTIFICATION_LOAD_OPTIONS)
            .where(Notification.uuid == notification_uuid)
        )
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        notification_obj: Notification,
        session: AsyncSession,
    ) -> Notification:

        session.add(notification_obj)
        await session.flush()

        return notification_obj

    @staticmethod
    async def update(
        notification_obj: Notification,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> Notification:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(notification_obj, field):
                setattr(notification_obj, field, value)

        await session.commit()

        return await NotificationRepository.get(notification_obj.uuid, session)  # type: ignore[return-value]

    @staticmethod
    async def get_all_for_user(
        recipient_user_uuid: UUID,
        filters: NotificationFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Notification]:

        conditions = NotificationRepository._build_conditions(
            filters.model_dump(exclude_none=True),
        )

        stmt = (
            select(Notification)
            .options(*NOTIFICATION_LOAD_OPTIONS)
            .where(
                Notification.recipient_user_uuid == recipient_user_uuid,
                *conditions,
            )
            .order_by(Notification.created_at.desc(), Notification.uuid.desc())
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit)

        result = await session.execute(stmt)

        return result.scalars().unique().all()
