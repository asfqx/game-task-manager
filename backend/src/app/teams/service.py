from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.lvls.schema import LvlSummaryResponse
from app.lvls.service import LvlService
from app.projects.repository import ProjectRepository
from app.system_logging.service import SystemLoggingService
from app.teams.filter import TeamFilterQueryParams
from app.teams.model import Team, TeamMember
from app.teams.repository import TeamRepository
from app.teams.schema import (
    AddTeamMemberRequest,
    CreateTeamRequest,
    TeamMemberResponse,
    TeamProjectResponse,
    TeamResponse,
    UpdateTeamRequest,
)
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schema import UserShortResponse


class TeamService:

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
    def _serialize_lvl(team_member: TeamMember) -> LvlSummaryResponse | None:

        if team_member.lvl is None:
            return None

        return LvlSummaryResponse(
            uuid=team_member.lvl.uuid,
            value=team_member.lvl.value,
            required_xp=team_member.lvl.required_xp,
        )

    @classmethod
    def _serialize_member(
        cls,
        member: TeamMember,
        team: Team,
    ) -> TeamMemberResponse:

        return TeamMemberResponse(
            uuid=member.uuid,
            user_uuid=member.user_uuid,
            user=cls._serialize_user(member.user),
            added_by_uuid=member.added_by_uuid,
            added_by=cls._serialize_user(member.added_by),
            lvl_uuid=member.lvl_uuid,
            lvl=cls._serialize_lvl(member),
            xp_amount=member.xp_amount,
            joined_at=member.joined_at,
            is_team_lead=member.user_uuid == team.lead_uuid,
        )

    @classmethod
    def _serialize_team(
        cls,
        team: Team,
    ) -> TeamResponse:

        members = sorted(
            team.members,
            key=lambda member: (
                member.user_uuid != team.lead_uuid,
                member.user.fio.lower(),
            ),
        )

        return TeamResponse(
            uuid=team.uuid,
            project_uuid=team.project_uuid,
            project=TeamProjectResponse(
                uuid=team.project.uuid,
                title=team.project.title,
            ),
            name=team.name,
            description=team.description,
            lead_uuid=team.lead_uuid,
            lead=cls._serialize_user(team.lead),
            created_by_uuid=team.created_by_uuid,
            created_by=cls._serialize_user(team.created_by),
            members_count=len({member.user_uuid for member in team.members}),
            members=[cls._serialize_member(member, team) for member in members],
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    @staticmethod
    async def _get_team_or_404(
        team_uuid: UUID,
        session: AsyncSession,
    ) -> Team:

        team = await TeamRepository.get(team_uuid, session)

        if not team:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Команда не найдена",
            )

        return team

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_team(
        cls,
        data: CreateTeamRequest,
        current_user: User,
        session: AsyncSession,
    ) -> TeamResponse:

        project = await ProjectRepository.get(data.project_uuid, session)

        if not project:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Проект не найден",
            )

        if current_user.role != UserRole.ADMIN and project.creator_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для создания команды в проекте",
            )

        if data.lead_uuid and await UserRepository.get(data.lead_uuid, session) is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        member_uuids = list(dict.fromkeys(data.member_uuids))
        if data.lead_uuid and data.lead_uuid not in member_uuids:
            member_uuids.append(data.lead_uuid)

        for member_uuid in member_uuids:
            if await UserRepository.get(member_uuid, session) is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден",
                )

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

        return cls._serialize_team(created_team)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_teams(
        cls,
        current_user: User,
        filters: TeamFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[TeamResponse]:

        if current_user.role == UserRole.ADMIN:
            teams = await TeamRepository.get_all(filters, session)
        else:
            teams = await TeamRepository.get_accessible_for_user(
                current_user.uuid,
                filters,
                session,
            )

        return [cls._serialize_team(team) for team in teams]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_team_by_id(
        cls,
        team_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> TeamResponse:

        team = await cls._get_team_or_404(team_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and team.project.creator_uuid != current_user.uuid
            and team.lead_uuid != current_user.uuid
            and not any(member.user_uuid == current_user.uuid for member in team.members)
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра команды",
            )

        return cls._serialize_team(team)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_team(
        cls,
        team_uuid: UUID,
        data: UpdateTeamRequest,
        current_user: User,
        session: AsyncSession,
    ) -> TeamResponse:

        team = await cls._get_team_or_404(team_uuid, session)

        if current_user.role != UserRole.ADMIN and team.project.creator_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления командой",
            )

        if data.lead_uuid and await UserRepository.get(data.lead_uuid, session) is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        if data.lead_uuid:
            existing_membership = await TeamRepository.get_membership(
                team.uuid,
                data.lead_uuid,
                session,
            )
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
        updated_team = await TeamRepository.update(team, data, session)

        return cls._serialize_team(updated_team)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def add_member(
        cls,
        team_uuid: UUID,
        data: AddTeamMemberRequest,
        current_user: User,
        session: AsyncSession,
    ) -> TeamResponse:

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

        if await UserRepository.get(data.user_uuid, session) is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        existing_membership = await TeamRepository.get_membership(
            team.uuid,
            data.user_uuid,
            session,
        )

        if existing_membership is None:
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

        return cls._serialize_team(refreshed_team)  # type: ignore[arg-type]

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
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Участник не состоит в этой команде",
            )

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
