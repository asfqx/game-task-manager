from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.lvls.model import Lvl
from app.lvls.repository import LvlRepository
from app.lvls.schema import CreateLvlRequest, UpdateLvlRequest
from app.system_logging.service import SystemLoggingService
from app.teams.model import TeamMember
from app.users.model import User


class LvlService:

    @staticmethod
    async def get_entry_level(
        session: AsyncSession,
    ) -> Lvl | None:

        return await LvlRepository.get_entry_level(session)

    @staticmethod
    async def resolve_level_for_xp(
        xp_amount: int,
        session: AsyncSession,
    ) -> Lvl | None:

        return await LvlRepository.get_for_xp(xp_amount, session)

    @staticmethod
    async def assign_level_for_team_member(
        team_member: TeamMember,
        session: AsyncSession,
    ) -> Lvl | None:

        lvl = await LvlRepository.get_for_xp(team_member.xp_amount, session)
        team_member.lvl_uuid = lvl.uuid if lvl else None
        team_member.lvl = lvl
        await session.flush()

        return lvl

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_default_lvl(
        session: AsyncSession,
    ) -> None:

        existing_lvl = await LvlRepository.get_entry_level(session)

        if existing_lvl:
            return

        await LvlRepository.create(
            Lvl(
                value="1",
                required_xp=0,
            ),
            session,
        )

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_all(
        session: AsyncSession,
    ) -> Sequence[Lvl]:

        return await LvlRepository.get_all(session)

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_by_id(
        lvl_uuid: UUID,
        session: AsyncSession,
    ) -> Lvl:

        lvl = await LvlRepository.get(lvl_uuid, session)

        if not lvl:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Уровень не найден",
            )

        return lvl

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_lvl(
        data: CreateLvlRequest,
        current_user: User,
        session: AsyncSession,
    ) -> Lvl:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления уровнями",
            )

        lvl_by_value = await LvlRepository.get_by_value(data.value, session)
        if lvl_by_value:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Уровень с таким названием уже существует",
            )

        lvl_by_required_xp = await LvlRepository.get_by_required_xp(data.required_xp, session)
        if lvl_by_required_xp:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Уровень с таким порогом XP уже существует",
            )

        lvl = await LvlRepository.create(
            Lvl(
                value=data.value,
                required_xp=data.required_xp,
            ),
            session,
        )
        await SystemLoggingService.log_user_action(
            session,
            action="lvl_created",
            actor_user_uuid=current_user.uuid,
            entity_type="lvl",
            entity_uuid=lvl.uuid,
            details={"value": lvl.value, "required_xp": lvl.required_xp},
        )

        result = await session.execute(select(TeamMember))
        team_members = result.scalars().all()

        for team_member in team_members:
            recalculated_lvl = await LvlRepository.get_for_xp(team_member.xp_amount, session)
            team_member.lvl_uuid = recalculated_lvl.uuid if recalculated_lvl else None

        await session.commit()

        return lvl

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_lvl(
        lvl_uuid: UUID,
        data: UpdateLvlRequest,
        current_user: User,
        session: AsyncSession,
    ) -> Lvl:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления уровнями",
            )

        lvl = await LvlRepository.get(lvl_uuid, session)
        if not lvl:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Уровень не найден",
            )

        if data.value is not None:
            lvl_by_value = await LvlRepository.get_by_value(data.value, session)
            if lvl_by_value and lvl_by_value.uuid != lvl.uuid:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail="Уровень с таким названием уже существует",
                )

        if data.required_xp is not None:
            lvl_by_required_xp = await LvlRepository.get_by_required_xp(data.required_xp, session)
            if lvl_by_required_xp and lvl_by_required_xp.uuid != lvl.uuid:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail="Уровень с таким порогом XP уже существует",
                )

        await SystemLoggingService.log_user_action(
            session,
            action="lvl_updated",
            actor_user_uuid=current_user.uuid,
            entity_type="lvl",
            entity_uuid=lvl.uuid,
            details={"changed_fields": sorted(data.model_fields_set)},
            commit=False,
        )
        updated_lvl = await LvlRepository.update(lvl, data, session)

        result = await session.execute(select(TeamMember))
        team_members = result.scalars().all()

        for team_member in team_members:
            recalculated_lvl = await LvlRepository.get_for_xp(team_member.xp_amount, session)
            team_member.lvl_uuid = recalculated_lvl.uuid if recalculated_lvl else None

        await session.commit()

        return updated_lvl
