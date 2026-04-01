import datetime as dt
import json
from collections.abc import AsyncIterator, Sequence
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.cache import get_cache_adapter
from app.core import AsyncSessionLocal
from app.error_handler import handle_connection_errors, handle_model_errors
from app.notifications.filter import NotificationFilterQueryParams
from app.notifications.model import Notification
from app.notifications.repository import NotificationRepository
from app.notifications.schema import NotificationResponse
from app.users.model import User
from app.users.schema import UserShortResponse


class NotificationService:

    CHANNEL_PREFIX = "notifications"

    @classmethod
    def schedule(
        cls,
        background_tasks: BackgroundTasks | None,
        *,
        recipient_user_uuids: Sequence[UUID],
        sender_user_uuid: UUID | None,
        content: str,
    ) -> None:

        if background_tasks is None:
            return

        background_tasks.add_task(
            cls.send,
            recipient_user_uuids=recipient_user_uuids,
            sender_user_uuid=sender_user_uuid,
            content=content,
        )

    @classmethod
    async def send(
        cls,
        *,
        recipient_user_uuids: Sequence[UUID],
        sender_user_uuid: UUID | None,
        content: str,
    ) -> None:

        unique_recipient_user_uuids: list[UUID] = []
        seen_recipient_user_uuids: set[UUID] = set()

        for recipient_user_uuid in recipient_user_uuids:
            if sender_user_uuid is not None and recipient_user_uuid == sender_user_uuid:
                continue
            if recipient_user_uuid in seen_recipient_user_uuids:
                continue

            seen_recipient_user_uuids.add(recipient_user_uuid)
            unique_recipient_user_uuids.append(recipient_user_uuid)

        if not unique_recipient_user_uuids:
            return

        async with AsyncSessionLocal() as session:
            try:
                notification_uuids: list[UUID] = []

                for recipient_user_uuid in unique_recipient_user_uuids:
                    notification = await NotificationRepository.create(
                        Notification(
                            content=content,
                            recipient_user_uuid=recipient_user_uuid,
                            sender_user_uuid=sender_user_uuid,
                        ),
                        session,
                    )
                    notification_uuids.append(notification.uuid)

                await session.commit()

                cache_adapter = get_cache_adapter()

                for notification_uuid in notification_uuids:
                    notification = await NotificationRepository.get(
                        notification_uuid,
                        session,
                    )

                    if notification is None or notification.recipient_user_uuid is None:
                        continue
                    
                    notification_ser = NotificationResponse(
                        uuid=notification.uuid,
                        content=notification.content,
                        recipient_user_uuid=notification.recipient_user_uuid,
                        recipient_user=(
                            UserShortResponse(
                                uuid=notification.recipient_user.uuid,
                                username=notification.recipient_user.username,
                                fio=notification.recipient_user.fio,
                            ) if notification.recipient_user else None
                        ),
                        sender_user_uuid=notification.sender_user_uuid,
                        sender_user=(
                            UserShortResponse(
                                uuid=notification.sender_user.uuid,
                                username=notification.sender_user.username,
                                fio=notification.sender_user.fio,
                            ) if notification.sender_user else None
                        ),
                        created_at=notification.created_at,
                    )

                    await cache_adapter.publish(
                        f"{cls.CHANNEL_PREFIX}:{notification.recipient_user_uuid}",
                        {
                            "event": "notification",
                            "notification": notification_ser.model_dump(mode="json"),
                        },
                    )
            except Exception:
                await session.rollback()
                logger.exception(
                    "Background notification dispatch failed for recipients {}",
                    unique_recipient_user_uuids,
                )

    @classmethod
    async def stream_notifications(
        cls,
        current_user: User,
        request: Request,
    ) -> AsyncIterator[str]:

        cache_adapter = get_cache_adapter()
        channel = f"{cls.CHANNEL_PREFIX}:{current_user.uuid}"

        yield (
            "event: connected\n"
            f"data: {json.dumps({'event': 'connected', 'user_uuid': str(current_user.uuid)}, ensure_ascii=False)}\n\n"
        )

        async for message in cache_adapter.subscribe(channel):
            if await request.is_disconnected():
                break

            if message is None:
                yield (
                    "event: ping\n"
                    f"data: {json.dumps({'timestamp': dt.datetime.now(dt.UTC).isoformat()}, ensure_ascii=False)}\n\n"
                )
                continue

            yield f"event: notification\ndata: {message}\n\n"

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_notifications(
        cls,
        current_user: User,
        filters: NotificationFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[NotificationResponse]:

        notifications = await NotificationRepository.get_all_for_user(
            current_user.uuid,
            filters,
            session,
        )
        return [
            NotificationResponse(
                uuid=notification.uuid,
                content=notification.content,
                recipient_user_uuid=notification.recipient_user_uuid,
                recipient_user=(
                    UserShortResponse(
                        uuid=notification.recipient_user.uuid,
                        username=notification.recipient_user.username,
                        fio=notification.recipient_user.fio,
                    ) if notification.recipient_user else None
                ),
                sender_user_uuid=notification.sender_user_uuid,
                sender_user=(
                    UserShortResponse(
                        uuid=notification.sender_user.uuid,
                        username=notification.sender_user.username,
                        fio=notification.sender_user.fio,
                    ) if notification.sender_user else None
                ),
                created_at=notification.created_at,
            ) for notification in notifications
        ]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_notification_by_id(
        cls,
        notification_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> NotificationResponse:

        notification = await NotificationRepository.get(notification_uuid, session)

        if notification is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Уведомление не найдено",
            )

        if notification.recipient_user_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра уведомления",
            )

        return NotificationResponse(
            uuid=notification.uuid,
            content=notification.content,
            recipient_user_uuid=notification.recipient_user_uuid,
            recipient_user=(
                UserShortResponse(
                    uuid=notification.recipient_user.uuid,
                    username=notification.recipient_user.username,
                    fio=notification.recipient_user.fio,
                ) if notification.recipient_user else None
            ),
            sender_user_uuid=notification.sender_user_uuid,
            sender_user=(
                UserShortResponse(
                    uuid=notification.sender_user.uuid,
                    username=notification.sender_user.username,
                    fio=notification.sender_user.fio,
                ) if notification.sender_user else None
            ),
            created_at=notification.created_at,
        )
