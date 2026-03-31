from uuid import UUID

from fastapi import APIRouter, status

from app.core import DBSession
from app.lvls.schema import CreateLvlRequest, LvlResponse, UpdateLvlRequest
from app.lvls.service import LvlService
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[LvlResponse],
    summary="Получить список уровней",
)
async def get_lvls(
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> list:

    return list(await LvlService.get_all(session))


@router.get(
    "/{lvl_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=LvlResponse,
    summary="Получить уровень по UUID",
)
async def get_lvl_by_uuid(
    lvl_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
):

    return await LvlService.get_by_id(lvl_uuid, session)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=LvlResponse,
    summary="Создать уровень",
)
async def create_lvl(
    data: CreateLvlRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
):

    return await LvlService.create_lvl(data, user, session)


@router.patch(
    "/{lvl_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=LvlResponse,
    summary="Обновить уровень",
)
async def update_lvl(
    lvl_uuid: UUID,
    data: UpdateLvlRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
):

    return await LvlService.update_lvl(lvl_uuid, data, user, session)
