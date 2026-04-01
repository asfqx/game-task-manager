from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.lvls.service import LvlService
from app.projects.repository import ProjectRepository
from app.system_logging.service import SystemLoggingService
from app.teams.filter import TeamFilterQueryParams
from app.teams.model import Team, TeamMember
from app.teams.repository import TeamRepository
from app.teams.schema import AddTeamMemberRequest, CreateTeamRequest, UpdateTeamRequest
from app.users.model import User
from app.users.repository import UserRepository


class TeamService:

    @staticmethod
    async def _get_team_or_404(
        team_uuid: UUID,
        session: AsyncSession,
    ) -> Team:

        team = await TeamRepository.get(team_uuid, session)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Команда не найдена")

        return team

    @staticmethod
    async def _is_user_in_project_teams(
        project_uuid: UUID,
        user_uuid: UUID,
        session: AsyncSession,
    ) -> bool:

        membership_alias = TeamMember
        stmt = (
            select(Team.uuid)
            .outerjoin(membership_alias, membership_alias.team_uuid == Team.uuid)
            .where(
                Team.project_uuid == project_uuid,
                or_(
                    Team.lead_uuid == user_uuid,
                    membership_alias.user_uuid == user_uuid,
                ),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_team(
        cls,
        data: CreateTeamRequest,
        current_user: User,
        session: AsyncSession,
    ) -> Team:

        project = await ProjectRepository.get(data.project_uuid, session)
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        if current_user.role != UserRole.ADMIN and project.creator_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для создания команды в проекте",
            )

        if data.lead_uuid and await UserRepository.get(data.lead_uuid, session) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        member_uuids = list(dict.fromkeys(data.member_uuids))
        if data.lead_uuid and data.lead_uuid not in member_uuids:
            member_uuids.append(data.lead_uuid)

        for member_uuid in member_uuids:
            if await UserRepository.get(member_uuid, session) is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        entry_lvl = await LvlService.get_entry_level(session)
        team = Team(
            project_uuid=data.project_uuid,
            created_by_uuid=current_user.uuid,
            lead_uuid=data.lead_uuid,
            name=data.name,
            description=data.description,
        )

        created_team = await TeamRepository.create(
            team,
            member_uuids=member_uuids,
            added_by_uuid=current_user.uuid,
            lvl_uuid=entry_lvl.uuid if entry_lvl else None,
            session=session,
        )

        await SystemLoggingService.log_user_action(
            session,
            action="team_created",
            actor_user_uuid=current_user.uuid,
            entity_type="team",
            entity_uuid=created_team.uuid,
            details={"project_uuid": str(created_team.project_uuid), "name": created_team.name},
            commit=False,
        )
        for member_uuid in member_uuids:
            await SystemLoggingService.log_user_action(
                session,
                action="team_joined",
                actor_user_uuid=member_uuid,
                entity_type="team",
                entity_uuid=created_team.uuid,
                details={"added_by_user_uuid": str(current_user.uuid)},
                commit=False,
            )
        await session.commit()

        return created_team

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_teams(
        cls,
        current_user: User,
        filters: TeamFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Team]:

        if current_user.role == UserRole.ADMIN:
            return await TeamRepository.get_all(filters, session)

        return await TeamRepository.get_accessible_for_user(current_user.uuid, filters, session)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_team_by_id(
        cls,
        team_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> Team:

        return await cls._get_team_or_404(team_uuid, session)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_team(
        cls,
        team_uuid: UUID,
        data: UpdateTeamRequest,
        current_user: User,
        session: AsyncSession,
    ) -> Team:

        team = await cls._get_team_or_404(team_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and team.project.creator_uuid != current_user.uuid
            and team.lead_uuid != current_user.uuid
        ):
          raise HTTPException(
              status.HTTP_403_FORBIDDEN,
              detail="Недостаточно прав для управления командой",
          )

        if data.lead_uuid and await UserRepository.get(data.lead_uuid, session) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        if data.lead_uuid:
            existing_membership = await TeamRepository.get_membership(team.uuid, data.lead_uuid, session)
            if existing_membership is None:
                entry_lvl = await LvlService.get_entry_level(session)
                session.add(
                    TeamMember(
                        team_uuid=team.uuid,
                        user_uuid=data.lead_uuid,
                        added_by_uuid=current_user.uuid,
                        lvl_uuid=entry_lvl.uuid if entry_lvl else None,
                    ),
                )
                await SystemLoggingService.log_user_action(
                    session,
                    action="team_joined",
                    actor_user_uuid=data.lead_uuid,
                    entity_type="team",
                    entity_uuid=team.uuid,
                    details={"added_by_user_uuid": str(current_user.uuid)},
                    commit=False,
                )

        await SystemLoggingService.log_user_action(
            session,
            action="team_updated",
            actor_user_uuid=current_user.uuid,
            entity_type="team",
            entity_uuid=team.uuid,
            details={"changed_fields": sorted(data.model_fields_set)},
            commit=False,
        )
        return await TeamRepository.update(team, data, session)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def add_member(
        cls,
        team_uuid: UUID,
        data: AddTeamMemberRequest,
        current_user: User,
        session: AsyncSession,
    ) -> Team:

        team = await cls._get_team_or_404(team_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and team.project.creator_uuid != current_user.uuid
            and team.lead_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления участниками команды",
            )

        user = await UserRepository.get(data.user_uuid, session)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        existing_membership = await TeamRepository.get_membership(team.uuid, data.user_uuid, session)
        if existing_membership is not None or team.lead_uuid == data.user_uuid:
            refreshed_team = await TeamRepository.get(team.uuid, session)
            return refreshed_team  # type: ignore[return-value]

        if not await cls._is_user_in_project_teams(team.project_uuid, data.user_uuid, session):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Пользователь должен уже состоять в одной из команд проекта",
            )

        entry_lvl = await LvlService.get_entry_level(session)
        await TeamRepository.create_membership(
            TeamMember(
                team_uuid=team.uuid,
                user_uuid=data.user_uuid,
                added_by_uuid=current_user.uuid,
                lvl_uuid=entry_lvl.uuid if entry_lvl else None,
            ),
            session,
        )
        await SystemLoggingService.log_user_action(
            session,
            action="team_member_added",
            actor_user_uuid=current_user.uuid,
            entity_type="team",
            entity_uuid=team.uuid,
            details={"member_user_uuid": str(data.user_uuid)},
            commit=False,
        )
        await SystemLoggingService.log_user_action(
            session,
            action="team_joined",
            actor_user_uuid=data.user_uuid,
            entity_type="team",
            entity_uuid=team.uuid,
            details={"added_by_user_uuid": str(current_user.uuid)},
            commit=False,
        )
        await session.commit()

        refreshed_team = await TeamRepository.get(team.uuid, session)
        return refreshed_team  # type: ignore[return-value]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def remove_member(
        cls,
        team_uuid: UUID,
        user_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> None:

        team = await cls._get_team_or_404(team_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and team.project.creator_uuid != current_user.uuid
            and team.lead_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления участниками команды",
            )

        if team.lead_uuid == user_uuid:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить текущего тимлида из команды. Сначала смените тимлида",
            )

        membership = await TeamRepository.get_membership(team.uuid, user_uuid, session)
        if membership is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Участник не состоит в этой команде")

        await TeamRepository.delete_membership(membership, session)
        await SystemLoggingService.log_user_action(
            session,
            action="team_member_removed",
            actor_user_uuid=current_user.uuid,
            entity_type="team",
            entity_uuid=team.uuid,
            details={"member_user_uuid": str(user_uuid)},
            commit=False,
        )
        await SystemLoggingService.log_user_action(
            session,
            action="team_left",
            actor_user_uuid=user_uuid,
            entity_type="team",
            entity_uuid=team.uuid,
            details={"removed_by_user_uuid": str(current_user.uuid)},
            commit=False,
        )
        await session.commit()

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def leave_team(
        cls,
        team_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> None:

        team = await cls._get_team_or_404(team_uuid, session)
        membership = await TeamRepository.get_membership(team.uuid, current_user.uuid, session)

        if membership is None and team.lead_uuid != current_user.uuid:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не состоит в этой команде")

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
            details={"project_uuid": str(team.project_uuid)},
            commit=False,
        )
        await session.commit()
