from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core import DBSession
from app.system_logging.filter import UserActionLogFilterDepends
from app.system_logging.schema import UserActionLogResponse
from app.system_logging.service import SystemLoggingService
from app.users.dependency import get_current_admin
from app.users.model import User


router = APIRouter(prefix="/user-actions")


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[UserActionLogResponse],
    summary="Получить журнал действий пользователей",
)
async def get_user_action_logs(
    user: Annotated[User, Depends(get_current_admin)],
    filters: UserActionLogFilterDepends,
    session: DBSession,
) -> list[UserActionLogResponse]:

    return list(
        await SystemLoggingService.get_user_action_logs(
            current_user=user,
            filters=filters,
            session=session,
        )
    )
