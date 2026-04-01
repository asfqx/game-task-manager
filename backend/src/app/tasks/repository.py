from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enum import TaskStatus
from app.projects.model import Project
from app.tasks.filter import TaskFilterQueryParams
from app.tasks.model import Task
from app.tasks.type import TaskFilterPayload
from app.teams.model import Team, TeamMember


TASK_LOAD_OPTIONS = (
    selectinload(Task.team).selectinload(Team.project),
    selectinload(Task.team).selectinload(Team.members).selectinload(TeamMember.user),
    selectinload(Task.team).selectinload(Team.members).selectinload(TeamMember.lvl),
    selectinload(Task.issuer_user),
    selectinload(Task.assignee_user),
)


class TaskRepository:

    @staticmethod
    def _build_conditions(filters: TaskFilterPayload) -> list[Any]:

        filter_mapping: dict[str, Callable[[Any], Any]] = {
            "cursor": lambda value: Task.uuid > value,
            "team_uuid": lambda value: Task.team_uuid == value,
            "issuer_user_uuid": lambda value: Task.issuer_user_uuid == value,
            "assignee_user_uuid": lambda value: Task.assignee_user_uuid == value,
            "status": lambda value: Task.status == value,
        }

        return [
            filter_mapping[key](value)
            for key, value in filters.items()
            if key in filter_mapping and value is not None
        ]

    @staticmethod
    async def get(
        task_uuid: UUID,
        session: AsyncSession,
    ) -> Task | None:

        stmt = (
            select(Task)
            .options(*TASK_LOAD_OPTIONS)
            .where(Task.uuid == task_uuid)
        )
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        filters: TaskFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Task]:

        conditions = TaskRepository._build_conditions(filters.model_dump(exclude_none=True))

        stmt = (
            select(Task)
            .options(*TASK_LOAD_OPTIONS)
            .where(*conditions)
            .order_by(Task.uuid)
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def get_accessible_for_user(
        user_uuid: UUID,
        filters: TaskFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[Task]:

        conditions = TaskRepository._build_conditions(filters.model_dump(exclude_none=True))

        stmt = (
            select(Task)
            .options(*TASK_LOAD_OPTIONS)
            .join(Team, Team.uuid == Task.team_uuid)
            .join(Project, Project.uuid == Team.project_uuid)
            .where(
                or_(
                    Project.creator_uuid == user_uuid,
                    Team.lead_uuid == user_uuid,
                    Task.assignee_user_uuid == user_uuid,
                ),
                *conditions,
            )
            .order_by(Task.uuid)
            .distinct()
        )

        if filters.limit:
            stmt = stmt.limit(filters.limit + 1)

        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def get_completed_by_assignee(
        user_uuid: UUID,
        session: AsyncSession,
    ) -> Sequence[Task]:

        stmt = (
            select(Task)
            .options(*TASK_LOAD_OPTIONS)
            .where(
                Task.assignee_user_uuid == user_uuid,
                Task.status == TaskStatus.DONE,
            )
            .order_by(Task.completed_at.desc().nullslast(), Task.updated_at.desc())
        )
        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    async def create(
        task_obj: Task,
        session: AsyncSession,
    ) -> Task:

        session.add(task_obj)
        await session.commit()

        return await TaskRepository.get(task_obj.uuid, session)  # type: ignore[return-value]

    @staticmethod
    async def update(
        task_obj: Task,
        new_data: BaseModel,
        session: AsyncSession,
    ) -> Task:

        update_dict = new_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(task_obj, field):
                setattr(task_obj, field, value)

        await session.commit()

        return await TaskRepository.get(task_obj.uuid, session)  # type: ignore[return-value]
