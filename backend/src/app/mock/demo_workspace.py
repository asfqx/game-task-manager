import datetime as dt
from uuid import UUID

from loguru import logger
from pydantic import BaseModel

from app.core import AsyncSessionLocal
from app.lvls.repository import LvlRepository
from app.projects.filter import ProjectFilterQueryParams
from app.projects.model import Project
from app.projects.repository import ProjectRepository
from app.tasks.filter import TaskFilterQueryParams
from app.tasks.model import Task
from app.tasks.repository import TaskRepository
from app.teams.filter import TeamFilterQueryParams
from app.teams.model import Team, TeamMember
from app.teams.repository import TeamRepository
from app.users.model import User
from app.users.repository import UserRepository

from .constants import (
    DEMO_PROJECT_DESCRIPTION,
    DEMO_PROJECT_TITLE,
    DEMO_TASKS,
    DEMO_TEAM_DESCRIPTION,
    DEMO_TEAM_NAME,
    DEMO_USERS,
)
from .seed_helpers import ensure_seed_user


class ProjectSeedUpdatePayload(BaseModel):
    title: str
    description: str | None


class TeamSeedUpdatePayload(BaseModel):
    name: str
    description: str | None
    lead_uuid: UUID
    created_by_uuid: UUID


async def seed_demo_workspace(owner: User) -> None:
    async with AsyncSessionLocal() as session:
        exist_owner = await UserRepository.get(owner.uuid, session)
        if exist_owner is None:
            logger.error("Не удалось найти суперпользователя для заполнения стартовых данных")
            return

        seeded_users: dict[str, User] = {}
        for username, email, fio in DEMO_USERS:
            seeded_users[username] = await ensure_seed_user(
                session,
                username=username,
                email=email,
                fio=fio,
                password=f"{username}_pass",
            )

        existing_projects = await ProjectRepository.get_all(
            ProjectFilterQueryParams(
                creator_uuid=owner.uuid,
                title=DEMO_PROJECT_TITLE,
            ),
            session=session,
        )
        project = next(iter(existing_projects), None)

        if project is None:
            project = await ProjectRepository.create(
                Project(
                    title=DEMO_PROJECT_TITLE,
                    description=DEMO_PROJECT_DESCRIPTION,
                    creator_uuid=owner.uuid,
                ),
                session=session,
            )
        else:
            project = await ProjectRepository.update(
                project,
                ProjectSeedUpdatePayload(
                    title=DEMO_PROJECT_TITLE,
                    description=DEMO_PROJECT_DESCRIPTION,
                ),
                session=session,
            )

        teamlead = seeded_users["teamlead1"]
        member_ids = [
            teamlead.uuid,
            *(user.uuid for user in seeded_users.values() if user.uuid != teamlead.uuid),
        ]

        existing_teams = await TeamRepository.get_all(
            TeamFilterQueryParams(
                project_uuid=project.uuid,
                name=DEMO_TEAM_NAME,
            ),
            session=session,
        )
        team = next(iter(existing_teams), None)

        if team is None:
            team = await TeamRepository.create(
                Team(
                    project_uuid=project.uuid,
                    created_by_uuid=owner.uuid,
                    lead_uuid=teamlead.uuid,
                    name=DEMO_TEAM_NAME,
                    description=DEMO_TEAM_DESCRIPTION,
                ),
                member_uuids=member_ids,
                added_by_uuid=owner.uuid,
                lvl_uuid=None,
                session=session,
            )
        else:
            team = await TeamRepository.update(
                team,
                TeamSeedUpdatePayload(
                    name=DEMO_TEAM_NAME,
                    description=DEMO_TEAM_DESCRIPTION,
                    lead_uuid=teamlead.uuid,
                    created_by_uuid=owner.uuid,
                ),
                session=session,
            )

        entry_level = await LvlRepository.get_entry_level(session)
        for user_uuid in member_ids:
            membership = await TeamRepository.get_membership(
                team.uuid,
                user_uuid,
                session=session,
            )
            if membership is None:
                await TeamRepository.create_membership(
                    TeamMember(
                        team_uuid=team.uuid,
                        user_uuid=user_uuid,
                        added_by_uuid=owner.uuid,
                        lvl_uuid=entry_level.uuid if entry_level else None,
                    ),
                    session=session,
                )

        now = dt.datetime.now(dt.UTC)
        for title, description, assignee_username, xp_amount, deadline_days in DEMO_TASKS:
            assignee = seeded_users[assignee_username]
            existing_tasks = await TaskRepository.get_all(
                TaskFilterQueryParams(
                    team_uuid=team.uuid,
                    assignee_user_uuid=assignee.uuid,
                ),
                session=session,
            )
            task = next(
                (existing_task for existing_task in existing_tasks if existing_task.title == title),
                None,
            )

            if task is not None:
                continue

            await TaskRepository.create(
                Task(
                    team_uuid=team.uuid,
                    issuer_user_uuid=teamlead.uuid,
                    assignee_user_uuid=assignee.uuid,
                    title=title,
                    description=description,
                    xp_amount=xp_amount,
                    deadline=now + dt.timedelta(days=deadline_days),
                ),
                session=session,
            )

        logger.success("Стартовые проект, команда, пользователи и задачи подготовлены")
