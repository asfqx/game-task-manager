from uuid import UUID

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from app.core import DBSession
from app.notifications.filter import NotificationFilterDepends
from app.notifications.schema import NotificationResponse
from app.notifications.service import NotificationService
from app.users.dependency import AuthenticatedActiveStreamUser, AuthenticatedActiveUser


router = APIRouter()


@router.get(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Подписаться на поток уведомлений",
)
async def stream_notifications(
    request: Request,
    user: AuthenticatedActiveStreamUser,
) -> StreamingResponse:

    return StreamingResponse(
        NotificationService.stream_notifications(
            current_user=user,
            request=request,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[NotificationResponse],
    summary="Получить уведомления текущего пользователя",
)
async def get_notifications(
    user: AuthenticatedActiveUser,
    filters: NotificationFilterDepends,
    session: DBSession,
) -> list[NotificationResponse]:

    return await NotificationService.get_notifications(
            current_user=user,
            filters=filters,
            session=session,
        )


@router.get(
    "/{notification_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=NotificationResponse,
    summary="Получить уведомление по UUID",
)
async def get_notification_by_uuid(
    notification_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> NotificationResponse:

    return await NotificationService.get_notification_by_id(
        notification_uuid=notification_uuid,
        current_user=user,
        session=session,
    )
