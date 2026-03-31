from fastapi import APIRouter, status

from app.core import DBSession
from app.system_logging.filter import XpAccrualLogFilterDepends
from app.system_logging.schema import XpAccrualLogResponse
from app.system_logging.service import SystemLoggingService
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter(prefix="/xp")


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[XpAccrualLogResponse],
    summary="Получить журнал начисления XP",
)
async def get_xp_logs(
    user: AuthenticatedActiveUser,
    filters: XpAccrualLogFilterDepends,
    session: DBSession,
) -> list[XpAccrualLogResponse]:

    return list(
        await SystemLoggingService.get_xp_logs(
            current_user=user,
            filters=filters,
            session=session,
        )
    )
