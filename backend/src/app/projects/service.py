from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.projects.filter import ProjectFilterQueryParams
from app.projects.model import Project
from app.projects.repository import ProjectRepository
from app.projects.schema import (
    CreateProjectRequest,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectTeamSummaryResponse,
    UpdateProjectRequest,
)
from app.system_logging.service import SystemLoggingService
from app.teams.model import Team
from app.users.model import User
from app.users.schema import UserShortResponse


class ProjectService:

    @classmethod
    def _can_view_team(
        cls,
        current_user: User,
        team: Team,
    ) -> bool:

        if current_user.role == UserRole.ADMIN:
            return True

        if team.project.creator_uuid == current_user.uuid:
            return True

        if team.lead_uuid == current_user.uuid:
            return True

        return any(member.user_uuid == current_user.uuid for member in team.members)

    @staticmethod
    def _serialize_user(user: User | None) -> UserShortResponse | None:

        if user is None:
            return None

        return UserShortResponse(
            uuid=user.uuid,
            username=user.username,
            fio=user.fio,
        )

    @staticmethod
    def _serialize_team_summary(team: Team) -> ProjectTeamSummaryResponse:

        return ProjectTeamSummaryResponse(
            uuid=team.uuid,
            name=team.name,
            description=team.description,
            lead_uuid=team.lead_uuid,
            lead_name=team.lead.fio if team.lead else None,
            members_count=len({member.user_uuid for member in team.members}),
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    @classmethod
    def _serialize_project(
        cls,
        project: Project,
        current_user: User,
        *,
        include_teams: bool,
    ) -> ProjectResponse | ProjectDetailResponse:

        accessible_teams = [
            team
            for team in project.teams
            if cls._can_view_team(current_user, team)
        ]

        if include_teams:
            return ProjectDetailResponse(
                uuid=project.uuid,
                title=project.title,
                description=project.description,
                creator_uuid=project.creator_uuid,
                creator=cls._serialize_user(project.creator),
                teams_count=len(accessible_teams),
                created_at=project.created_at,
                updated_at=project.updated_at,
                teams=[
                    cls._serialize_team_summary(team)
                    for team in accessible_teams
                ],
            )

        return ProjectResponse(
            uuid=project.uuid,
            title=project.title,
            description=project.description,
            creator_uuid=project.creator_uuid,
            creator=cls._serialize_user(project.creator),
            teams_count=len(accessible_teams),
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_project(
        cls,
        data: CreateProjectRequest,
        current_user: User,
        session: AsyncSession,
    ) -> ProjectDetailResponse:

        project = Project(
            title=data.title,
            description=data.description,
            creator_uuid=current_user.uuid,
        )

        created_project = await ProjectRepository.create(project, session)
        await SystemLoggingService.log_user_action(
            session,
            action="project_created",
            actor_user_uuid=current_user.uuid,
            entity_type="project",
            entity_uuid=created_project.uuid,
            details={"title": created_project.title},
        )

        return cls._serialize_project(
            created_project,
            current_user,
            include_teams=True,
        )

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_projects(
        cls,
        current_user: User,
        filters: ProjectFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[ProjectResponse]:

        if current_user.role == UserRole.ADMIN:
            projects = await ProjectRepository.get_all(filters, session)
        else:
            projects = await ProjectRepository.get_accessible_for_user(
                current_user.uuid,
                filters,
                session,
            )

        return [
            cls._serialize_project(project, current_user, include_teams=False)
            for project in projects
        ]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_project_by_id(
        cls,
        project_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> ProjectDetailResponse:

        project = await ProjectRepository.get(project_uuid, session)

        if not project:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Проект не найден",
            )

        if (
            current_user.role != UserRole.ADMIN
            and project.creator_uuid != current_user.uuid
            and not any(cls._can_view_team(current_user, team) for team in project.teams)
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра проекта",
            )

        return cls._serialize_project(project, current_user, include_teams=True)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_project(
        cls,
        project_uuid: UUID,
        data: UpdateProjectRequest,
        current_user: User,
        session: AsyncSession,
    ) -> ProjectDetailResponse:

        project = await ProjectRepository.get(project_uuid, session)

        if not project:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Проект не найден",
            )

        if current_user.role != UserRole.ADMIN and project.creator_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления проектом",
            )

        await SystemLoggingService.log_user_action(
            session,
            action="project_updated",
            actor_user_uuid=current_user.uuid,
            entity_type="project",
            entity_uuid=project.uuid,
            details={"changed_fields": sorted(data.model_fields_set)},
            commit=False,
        )
        updated_project = await ProjectRepository.update(project, data, session)

        return cls._serialize_project(
            updated_project,
            current_user,
            include_teams=True,
        )
