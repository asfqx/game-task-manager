from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core import DBSession
from app.teams.filter import TeamFilterDepends
from app.teams.schema import (
    AddTeamMemberRequest,
    CreateTeamRequest,
    TeamResponse,
    UpdateTeamRequest,
)
from app.teams.service import TeamService
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[TeamResponse],
    summary="Получить доступные команды",
)
async def get_teams(
    user: AuthenticatedActiveUser,
    filters: TeamFilterDepends,
    session: DBSession,
) -> list[TeamResponse]:

    return list(
        await TeamService.get_teams(
            current_user=user,
            filters=filters,
            session=session,
        )
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TeamResponse,
    summary="Создать команду",
)
async def create_team(
    data: CreateTeamRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> TeamResponse:

    return await TeamService.create_team(
        data=data,
        current_user=user,
        session=session,
    )


@router.get(
    "/{team_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=TeamResponse,
    summary="Получить команду по UUID",
)
async def get_team_by_uuid(
    team_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> TeamResponse:

    return await TeamService.get_team_by_id(
        team_uuid=team_uuid,
        current_user=user,
        session=session,
    )


@router.patch(
    "/{team_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=TeamResponse,
    summary="Обновить команду",
)
async def update_team(
    team_uuid: UUID,
    data: UpdateTeamRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> TeamResponse:

    return await TeamService.update_team(
        team_uuid=team_uuid,
        data=data,
        current_user=user,
        session=session,
    )


@router.post(
    "/{team_uuid}/members",
    status_code=status.HTTP_200_OK,
    response_model=TeamResponse,
    summary="Добавить участника в команду",
)
async def add_team_member(
    team_uuid: UUID,
    data: AddTeamMemberRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> TeamResponse:

    return await TeamService.add_member(
        team_uuid=team_uuid,
        data=data,
        current_user=user,
        session=session,
    )


@router.delete(
    "/{team_uuid}/members/{user_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить участника из команды",
)
async def remove_team_member(
    team_uuid: UUID,
    user_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> Response:

    await TeamService.remove_member(
        team_uuid=team_uuid,
        user_uuid=user_uuid,
        current_user=user,
        session=session,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
