import datetime as dt

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.schemas.auth import CreateSuperuserRequest
from app.core import AsyncSessionLocal
from app.enum import UserRole, UserStatus
from app.lvls.repository import LvlRepository
from app.projects.model import Project
from app.security import Argon2Hasher
from app.tasks.model import Task
from app.teams.model import Team, TeamMember
from app.users.model import User
from app.users.repository import UserRepository


DEMO_PROJECT_TITLE = "Demo Project"
DEMO_TEAM_NAME = "Core Team"
DEMO_USERS: tuple[tuple[str, str, str], ...] = (
    ("teamlead1", "teamlead1@example.com", "TeamLead One"),
    ("alicework", "alicework@example.com", "Alice Workman"),
    ("bobworker", "bobworker@example.com", "Bob Worker"),
    ("charlie8", "charlie8@example.com", "Charlie Ray"),
)
DEMO_TASKS: tuple[tuple[str, str, str, int, int], ...] = (
    ("Prepare backlog", "Собрать и описать стартовый бэклог проекта.", "alicework", 120, 3),
    ("Design board", "Подготовить структуру доски задач и статусов.", "bobworker", 180, 5),
    ("Setup notifications", "Проверить уведомления и сценарии оповещений.", "charlie8", 220, 7),
)


async def _ensure_seed_user(
    session,
    *,
    username: str,
    email: str,
    fio: str,
    password: str,
    role: UserRole = UserRole.USER,
    email_confirmed: bool = True,
) -> User:

    user = await UserRepository.get_by_login(email, session=session)

    if user is None:
        user = User(
            email=email,
            username=username,
            fio=fio,
            role=role,
            password_hash=Argon2Hasher.hash(password),
            email_confirmed=email_confirmed,
            status=UserStatus.ACTIVE,
        )
        session.add(user)
        await session.flush()
        return user

    user.username = username
    user.fio = fio
    user.role = role
    user.status = UserStatus.ACTIVE
    user.email_confirmed = email_confirmed
    if not Argon2Hasher.verify(password, user.password_hash):
        user.password_hash = Argon2Hasher.hash(password)

    await session.flush()
    return user


async def _seed_demo_workspace(owner: User) -> None:

    async with AsyncSessionLocal() as session:
        exist_owner = await UserRepository.get(owner.uuid, session)
        if exist_owner is None:
            logger.error("Не удалось найти суперюзера для заполнения стартовых данных")
            return

        seeded_users: dict[str, User] = {}
        for username, email, fio in DEMO_USERS:
            seeded_users[username] = await _ensure_seed_user(
                session,
                username=username,
                email=email,
                fio=fio,
                password=f"{username}_pass",
            )

        project = (
            await session.execute(
                select(Project).where(
                    Project.creator_uuid == owner.uuid,
                    Project.title == DEMO_PROJECT_TITLE,
                )
            )
        ).scalar_one_or_none()

        if project is None:
            project = Project(
                title=DEMO_PROJECT_TITLE,
                description="Стартовый проект для демонстрации ролей, команд и задач.",
                creator_uuid=owner.uuid,
            )
            session.add(project)
            await session.flush()

        teamlead = seeded_users["teamlead1"]
        team = (
            await session.execute(
                select(Team).where(
                    Team.project_uuid == project.uuid,
                    Team.name == DEMO_TEAM_NAME,
                )
            )
        ).scalar_one_or_none()

        if team is None:
            team = Team(
                project_uuid=project.uuid,
                created_by_uuid=owner.uuid,
                lead_uuid=teamlead.uuid,
                name=DEMO_TEAM_NAME,
                description="Основная команда стартового проекта.",
            )
            session.add(team)
            await session.flush()
        else:
            team.created_by_uuid = owner.uuid
            team.lead_uuid = teamlead.uuid
            await session.flush()

        entry_level = await LvlRepository.get_entry_level(session)
        member_ids = [teamlead.uuid, *(user.uuid for user in seeded_users.values() if user.uuid != teamlead.uuid)]

        for user_uuid in member_ids:
            membership = (
                await session.execute(
                    select(TeamMember).where(
                        TeamMember.team_uuid == team.uuid,
                        TeamMember.user_uuid == user_uuid,
                    )
                )
            ).scalar_one_or_none()

            if membership is None:
                session.add(
                    TeamMember(
                        team_uuid=team.uuid,
                        user_uuid=user_uuid,
                        added_by_uuid=owner.uuid,
                        lvl_uuid=entry_level.uuid if entry_level else None,
                    )
                )

        await session.flush()

        now = dt.datetime.now(dt.UTC)
        for title, description, assignee_username, xp_amount, deadline_days in DEMO_TASKS:
            assignee = seeded_users[assignee_username]
            task = (
                await session.execute(
                    select(Task).where(
                        Task.team_uuid == team.uuid,
                        Task.title == title,
                        Task.assignee_user_uuid == assignee.uuid,
                    )
                )
            ).scalar_one_or_none()

            if task is not None:
                continue

            session.add(
                Task(
                    team_uuid=team.uuid,
                    issuer_user_uuid=teamlead.uuid,
                    assignee_user_uuid=assignee.uuid,
                    title=title,
                    description=description,
                    xp_amount=xp_amount,
                    deadline=now + dt.timedelta(days=deadline_days),
                )
            )

        await session.commit()
        logger.success("Стартовые проект, команда, пользователи и задачи подготовлены")


async def create_first_superuser() -> None:
    from app.auth.services import AuthService

    register_data = CreateSuperuserRequest(
        email="root@example.com",
        username="rootadmin",
        password="strongpass123",
        fio="Root Admin",
    )

    async with AsyncSessionLocal() as session:
        existing_user = await UserRepository.get_by_login(
            register_data.email,
            session=session,
        )

        if existing_user is None:
            try:
                await AuthService.create_superuser(data=register_data, session=session)
                logger.success(
                    f"Суперпользователь создан успешно: email={register_data.email}, username={register_data.username}"
                )
            except IntegrityError:
                await session.rollback()
                logger.error(
                    "Ошибка БД при создании суперпользователя (возможно, дублирование)",
                )
        else:
            if not Argon2Hasher.verify(register_data.password, existing_user.password_hash):
                existing_user.password_hash = Argon2Hasher.hash(register_data.password)
            existing_user.status = UserStatus.ACTIVE
            existing_user.email_confirmed = True
            existing_user.role = UserRole.ADMIN
            await session.commit()
            logger.info("Суперпользователь уже существует")

        owner = await UserRepository.get_by_login(register_data.email, session=session)

    if owner is not None:
        await _seed_demo_workspace(owner)
