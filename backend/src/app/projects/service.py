from typing import Any, Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.projects.filter import ProjectFilterQueryParams
from app.projects.model import Project
from app.projects.repository import ProjectRepository
from app.projects.schema import CreateProjectRequest, UpdateProjectRequest
from app.system_logging.service import SystemLoggingService
from app.teams.repository import TeamRepository
from app.users.model import User


class ProjectService:

    @staticmethod
    async def _has_project_access(
        project: Project,
        current_user: User,
        session: AsyncSession,
    ) -> bool:
        if current_user.role == UserRole.ADMIN or project.creator_uuid == current_user.uuid:
            return True

        accessible_projects = await ProjectRepository.get_accessible_for_user(
            current_user.uuid,
            ProjectFilterQueryParams(),
            session,
        )
        return any(candidate.uuid == project.uuid for candidate in accessible_projects)

    @classmethod
    def _build_project_payload(
        cls,
        project: Project,
        current_user: User,
        *,
        include_teams: bool,
    ) -> dict[str, Any]:

        accessible_teams = list(project.teams)

        payload = {
            "uuid": project.uuid,
            "title": project.title,
            "description": project.description,
            "creator_uuid": project.creator_uuid,
            "creator": project.creator,
            "teams_count": len(accessible_teams),
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }

        if include_teams:
            payload["teams"] = accessible_teams

        return payload

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_project(
        cls,
        data: CreateProjectRequest,
        current_user: User,
        session: AsyncSession,
    ) -> dict:

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

        return cls._build_project_payload(created_project, current_user, include_teams=True)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_projects(
        cls,
        current_user: User,
        filters: ProjectFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[dict]:

        if current_user.role == UserRole.ADMIN:
            projects = await ProjectRepository.get_all(filters, session)
        else:
            projects = await ProjectRepository.get_accessible_for_user(current_user.uuid, filters, session)

        return [cls._build_project_payload(project, current_user, include_teams=False) for project in projects]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_project_by_id(
        cls,
        project_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> dict:

        project = await ProjectRepository.get(project_uuid, session)
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        if not await cls._has_project_access(project, current_user, session):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра проекта",
            )

        return cls._build_project_payload(project, current_user, include_teams=True)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_project(
        cls,
        project_uuid: UUID,
        data: UpdateProjectRequest,
        current_user: User,
        session: AsyncSession,
    ) -> dict:

        project = await ProjectRepository.get(project_uuid, session)
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        if current_user.role != UserRole.ADMIN and project.creator_uuid != current_user.uuid:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="У вас нет прав")

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

        return cls._build_project_payload(updated_project, current_user, include_teams=True)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def delete_project(
        cls,
        project_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> None:

        project = await ProjectRepository.get(project_uuid, session)
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        if current_user.role != UserRole.ADMIN and project.creator_uuid != current_user.uuid:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="У вас нет прав")

        await SystemLoggingService.log_user_action(
            session,
            action="project_deleted",
            actor_user_uuid=current_user.uuid,
            entity_type="project",
            entity_uuid=project.uuid,
            details={"title": project.title},
            commit=False,
        )
        await ProjectRepository.delete(project, session)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def leave_project(
        cls,
        project_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> None:

        project = await ProjectRepository.get(project_uuid, session)
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        if project.creator_uuid == current_user.uuid and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Вы не можете покинуть проект",
            )

        left_any_team = False

        for team in project.teams:
            membership = await TeamRepository.get_membership(team.uuid, current_user.uuid, session)
            if membership is None and team.lead_uuid != current_user.uuid:
                continue

            if team.lead_uuid == current_user.uuid:
                team.lead_uuid = None

            if membership is not None:
                await session.delete(membership)

            await SystemLoggingService.log_user_action(
                session,
                action="team_left",
                actor_user_uuid=current_user.uuid,
                entity_type="team",
                entity_uuid=team.uuid,
                details={"project_uuid": str(project.uuid)},
                commit=False,
            )
            left_any_team = True

        if not left_any_team:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Вы не можете покинуть проект",
            )

        await SystemLoggingService.log_user_action(
            session,
            action="project_left",
            actor_user_uuid=current_user.uuid,
            entity_type="project",
            entity_uuid=project.uuid,
            details={"title": project.title},
            commit=False,
        )
        await session.commit()
