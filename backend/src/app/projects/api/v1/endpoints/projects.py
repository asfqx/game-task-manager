from uuid import UUID

from fastapi import APIRouter, status

from app.core import DBSession
from app.projects.filter import ProjectFilterDepends
from app.projects.schema import (
    CreateProjectRequest,
    ProjectDetailResponse,
    ProjectResponse,
    UpdateProjectRequest,
)
from app.projects.service import ProjectService
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[ProjectResponse],
    summary="Получить доступные проекты",
)
async def get_projects(
    user: AuthenticatedActiveUser,
    filters: ProjectFilterDepends,
    session: DBSession,
) -> list[ProjectResponse]:

    return list(
        await ProjectService.get_projects(
            current_user=user,
            filters=filters,
            session=session,
        )
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectDetailResponse,
    summary="Создать проект",
)
async def create_project(
    data: CreateProjectRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> ProjectDetailResponse:

    return await ProjectService.create_project(
        data=data,
        current_user=user,
        session=session,
    )


@router.get(
    "/{project_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=ProjectDetailResponse,
    summary="Получить проект по UUID",
)
async def get_project_by_uuid(
    project_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> ProjectDetailResponse:

    return await ProjectService.get_project_by_id(
        project_uuid=project_uuid,
        current_user=user,
        session=session,
    )


@router.patch(
    "/{project_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=ProjectDetailResponse,
    summary="Обновить проект",
)
async def update_project(
    project_uuid: UUID,
    data: UpdateProjectRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> ProjectDetailResponse:

    return await ProjectService.update_project(
        project_uuid=project_uuid,
        data=data,
        current_user=user,
        session=session,
    )
