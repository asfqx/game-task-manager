from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.projects.model import Project
from app.teams.filter import TeamFilterQueryParams
from app.teams.model import Team, TeamMember
from app.teams.type import TeamFilterPayload


TEAM_LOAD_OPTIONS = (
    selectinload(Team.project),
    selectinload(Team.lead),
    selectinload(Team.created_by),
    selectinload(Team.members).selectinload(TeamMember.user),
    selectinload(Team.members).selectinload(TeamMember.added_by),
    selectinload(Team.members).selectinload(TeamMember.lvl),
)


class TeamRepository:

    @staticmethod
    def _build_conditions(filters: TeamFilterPayload) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "cursor": lambda value: Team.uuid > value,
            "project_uuid": lambda value: Team.project_uuid == value,
            "lead_uuid": lambda value: Team.lead_uuid == value,
            "name": lambda value: Team.name.ilike(f"%{value}%"),
        }

        return [
            filter_mapping[key](value)
            for key, value in filters.items()
            if key in filter_mapping and value is not None
        ]

    @staticmethod
    async def get(
        team_uuid: UUID,
        session: AsyncSession,
    ) -> Team | None:

        stmt = (
            select(Team)
            .options(*TEAM_LOAD_OPTIONS)
            .where(Team.uuid == team_uuid)
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        filters: TeamFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Team]:

        conditions = TeamRepository._build_conditions(
            filters.model_dump(exclude_none=True),
        )

        stmt = (
            select(Team)
            .options(*TEAM_LOAD_OPTIONS)
            .where(*conditions)
            .order_by(Team.uuid)
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def get_accessible_for_user(
        user_uuid: UUID,
        filters: TeamFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Team]:

        conditions = TeamRepository._build_conditions(
            filters.model_dump(exclude_none=True),
        )
        member_alias = aliased(TeamMember)

        stmt = (
            select(Team)
            .options(*TEAM_LOAD_OPTIONS)
            .join(Project, Project.uuid == Team.project_uuid)
            .outerjoin(member_alias, member_alias.team_uuid == Team.uuid)
            .where(
                or_(
                    Project.creator_uuid == user_uuid,
                    Team.lead_uuid == user_uuid,
                    member_alias.user_uuid == user_uuid,
                ),
                *conditions,
            )
            .order_by(Team.uuid)
            .distinct()
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def get_by_user(
        user_uuid: UUID,
        session: AsyncSession,
    ) -> Sequence[Team]:

        member_alias = aliased(TeamMember)

        stmt = (
            select(Team)
            .options(*TEAM_LOAD_OPTIONS)
            .outerjoin(member_alias, member_alias.team_uuid == Team.uuid)
            .where(
                or_(
                    Team.lead_uuid == user_uuid,
                    member_alias.user_uuid == user_uuid,
                ),
            )
            .order_by(Team.uuid)
            .distinct()
        )

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def get_membership(
        team_uuid: UUID,
        user_uuid: UUID,
        session: AsyncSession,
    ) -> TeamMember | None:

        stmt = select(TeamMember).where(
            TeamMember.team_uuid == team_uuid,
            TeamMember.user_uuid == user_uuid,
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        team_obj: Team,
        member_uuids: Sequence[UUID],
        added_by_uuid: UUID | None,
        lvl_uuid: UUID | None,
        session: AsyncSession,
    ) -> Team:

        session.add(team_obj)

        await session.flush()

        for member_uuid in member_uuids:
            session.add(
                TeamMember(
                    team_uuid=team_obj.uuid,
                    user_uuid=member_uuid,
                    added_by_uuid=added_by_uuid,
                    lvl_uuid=lvl_uuid,
                ),
            )

        await session.commit()

        return await TeamRepository.get(team_obj.uuid, session)  # type: ignore[return-value]

    @staticmethod
    async def update(
        team_obj: Team,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> Team:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(team_obj, field):
                setattr(team_obj, field, value)

        await session.commit()

        return await TeamRepository.get(team_obj.uuid, session)  # type: ignore[return-value]

    @staticmethod
    async def create_membership(
        membership: TeamMember,
        session: AsyncSession,
    ) -> TeamMember:

        session.add(membership)

        await session.commit()
        await session.refresh(membership)

        return membership

    @staticmethod
    async def delete_membership(
        membership: TeamMember,
        session: AsyncSession,
    ) -> None:

        await session.delete(membership)
        await session.commit()
