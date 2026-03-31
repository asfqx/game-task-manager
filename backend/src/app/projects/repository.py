from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.projects.filter import ProjectFilterQueryParams
from app.projects.model import Project
from app.projects.type import ProjectFilterPayload
from app.teams.model import Team, TeamMember


PROJECT_LOAD_OPTIONS = (
    selectinload(Project.creator),
    selectinload(Project.teams).selectinload(Team.lead),
    selectinload(Project.teams).selectinload(Team.members).selectinload(TeamMember.user),
)


class ProjectRepository:

    @staticmethod
    def _build_conditions(filters: ProjectFilterPayload) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "cursor": lambda value: Project.uuid > value,
            "creator_uuid": lambda value: Project.creator_uuid == value,
            "title": lambda value: Project.title.ilike(f"%{value}%"),
        }

        return [
            filter_mapping[key](value)
            for key, value in filters.items()
            if key in filter_mapping and value is not None
        ]

    @staticmethod
    async def get(
        project_uuid: UUID,
        session: AsyncSession,
    ) -> Project | None:

        stmt = (
            select(Project)
            .options(*PROJECT_LOAD_OPTIONS)
            .where(Project.uuid == project_uuid)
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        filters: ProjectFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Project]:

        conditions = ProjectRepository._build_conditions(
            filters.model_dump(exclude_none=True),
        )

        stmt = (
            select(Project)
            .options(*PROJECT_LOAD_OPTIONS)
            .where(*conditions)
            .order_by(Project.uuid)
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def get_accessible_for_user(
        user_uuid: UUID,
        filters: ProjectFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Project]:

        conditions = ProjectRepository._build_conditions(
            filters.model_dump(exclude_none=True),
        )
        member_alias = aliased(TeamMember)

        stmt = (
            select(Project)
            .options(*PROJECT_LOAD_OPTIONS)
            .outerjoin(Team, Team.project_uuid == Project.uuid)
            .outerjoin(member_alias, member_alias.team_uuid == Team.uuid)
            .where(
                or_(
                    Project.creator_uuid == user_uuid,
                    Team.lead_uuid == user_uuid,
                    member_alias.user_uuid == user_uuid,
                ),
                *conditions,
            )
            .order_by(Project.uuid)
            .distinct()
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def create(
        project_obj: Project,
        session: AsyncSession,
    ) -> Project:

        session.add(project_obj)

        await session.commit()

        return await ProjectRepository.get(project_obj.uuid, session)  # type: ignore[return-value]

    @staticmethod
    async def update(
        project_obj: Project,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> Project:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(project_obj, field):
                setattr(project_obj, field, value)

        await session.commit()

        return await ProjectRepository.get(project_obj.uuid, session)  # type: ignore[return-value]

    @staticmethod
    async def save(
        project_obj: Project,
        session: AsyncSession,
    ) -> Project:

        await session.commit()

        return await ProjectRepository.get(project_obj.uuid, session)  # type: ignore[return-value]
