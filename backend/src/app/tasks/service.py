import datetime as dt
from collections.abc import Sequence
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import AsyncSessionLocal
from app.enum import TaskStatus, UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.lvls.schema import LvlSummaryResponse
from app.lvls.service import LvlService
from app.notifications.service import NotificationService
from app.system_logging.model import XpAccrualLog
from app.system_logging.repository import XpAccrualLogRepository
from app.system_logging.service import SystemLoggingService
from app.system_logging.type import UserActionLogDetailsPayload
from app.tasks.filter import TaskFilterQueryParams
from app.tasks.model import Task
from app.tasks.repository import TaskRepository
from app.tasks.schema import (
    CreateTaskRequest,
    RejectTaskRequest,
    TaskAssigneeProgressResponse,
    TaskResponse,
    TaskTeamResponse,
    UpdateTaskRequest,
)
from app.teams.model import Team, TeamMember
from app.teams.repository import TeamRepository
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schema import UserShortResponse


class TaskRepositoryUpdatePayload(BaseModel):

    title: str | None = None
    description: str | None = None
    assignee_user_uuid: UUID | None = None
    xp_amount: int | None = None
    deadline: dt.datetime | None = None
    status: TaskStatus | None = None
    accepted_at: dt.datetime | None = None
    submitted_for_review_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    review_comment: str | None = None


class TaskService:

    @staticmethod
    def _serialize_task(task: Task) -> TaskResponse:

        assignee_membership = next(
            (
                member
                for member in task.team.members
                if member.user_uuid == task.assignee_user_uuid
            ),
            None,
        )

        return TaskResponse(
            uuid=task.uuid,
            team_uuid=task.team_uuid,
            team=TaskTeamResponse(
                uuid=task.team.uuid,
                name=task.team.name,
                project_uuid=task.team.project.uuid,
                project_title=task.team.project.title,
            ),
            issuer_user_uuid=task.issuer_user_uuid,
            issuer_user=(
                UserShortResponse(
                    uuid=task.issuer_user.uuid,
                    username=task.issuer_user.username,
                    fio=task.issuer_user.fio,
                )
                if task.issuer_user is not None
                else None
            ),
            assignee_user_uuid=task.assignee_user_uuid,
            assignee_user=(
                UserShortResponse(
                    uuid=task.assignee_user.uuid,
                    username=task.assignee_user.username,
                    fio=task.assignee_user.fio,
                )
                if task.assignee_user is not None
                else None
            ),
            title=task.title,
            description=task.description,
            review_comment=task.review_comment,
            xp_amount=task.xp_amount,
            status=task.status,
            deadline=task.deadline,
            accepted_at=task.accepted_at,
            submitted_for_review_at=task.submitted_for_review_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            assignee_team_progress=(
                TaskAssigneeProgressResponse(
                    xp_amount=assignee_membership.xp_amount,
                    lvl_uuid=assignee_membership.lvl_uuid,
                    lvl=(
                        LvlSummaryResponse(
                            uuid=assignee_membership.lvl.uuid,
                            value=assignee_membership.lvl.value,
                            required_xp=assignee_membership.lvl.required_xp,
                        )
                        if assignee_membership is not None and assignee_membership.lvl is not None
                        else None
                    ),
                )
                if assignee_membership is not None
                else None
            ),
        )

    @staticmethod
    async def _get_team_or_404(
        team_uuid: UUID,
        session: AsyncSession,
    ) -> Team:

        team = await TeamRepository.get(team_uuid, session)

        if team is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Команда не найдена",
            )

        return team

    @staticmethod
    async def _get_task_or_404(
        task_uuid: UUID,
        session: AsyncSession,
    ) -> Task:

        task = await TaskRepository.get(task_uuid, session)

        if task is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена",
            )

        return task

    @staticmethod
    async def _get_team_member_or_400(
        team_uuid: UUID,
        user_uuid: UUID,
        session: AsyncSession,
    ) -> TeamMember:

        team_member = await TeamRepository.get_membership(team_uuid, user_uuid, session)

        if team_member is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Исполнитель должен состоять в команде задачи",
            )

        return team_member

    @staticmethod
    async def _log_task_action(
        session: AsyncSession,
        *,
        action: str,
        actor_user_uuid: UUID | None,
        task_uuid: UUID,
        details: UserActionLogDetailsPayload | None = None,
    ) -> None:

        await SystemLoggingService.log_user_action(
            session,
            action=action,
            actor_user_uuid=actor_user_uuid,
            entity_type="task",
            entity_uuid=task_uuid,
            details=details,
            commit=False,
        )

    @classmethod
    async def process_task_xp_accrual(
        cls,
        task_uuid: UUID,
        issuer_user_uuid: UUID,
    ) -> None:

        async with AsyncSessionLocal() as session:
            try:
                task = await cls._get_task_or_404(task_uuid, session)

                if task.status != TaskStatus.DONE:
                    logger.warning(
                        "XP accrual skipped for task {} because task status is {}",
                        task_uuid,
                        task.status,
                    )
                    return

                existing_xp_log = await XpAccrualLogRepository.get_by_task_uuid(
                    task_uuid,
                    session,
                )
                if existing_xp_log is not None:
                    logger.info(
                        "XP accrual skipped for task {} because XP log already exists",
                        task_uuid,
                    )
                    return

                if task.assignee_user_uuid is None:
                    logger.warning(
                        "XP accrual skipped for task {} because assignee is missing",
                        task_uuid,
                    )
                    return

                team_member = await cls._get_team_member_or_400(
                    task.team_uuid,
                    task.assignee_user_uuid,
                    session,
                )

                previous_lvl_uuid = team_member.lvl_uuid
                team_member.xp_amount += task.xp_amount
                new_lvl = await LvlService.assign_level_for_team_member(
                    team_member,
                    session,
                )

                await XpAccrualLogRepository.create(
                    XpAccrualLog(
                        xp_amount=task.xp_amount,
                        recipient_user_uuid=task.assignee_user_uuid,
                        issuer_user_uuid=issuer_user_uuid,
                        task_uuid=task.uuid,
                    ),
                    session,
                )

                await session.commit()

                if previous_lvl_uuid != team_member.lvl_uuid and new_lvl is not None:
                    await NotificationService.send(
                        recipient_user_uuids=[task.assignee_user_uuid],
                        sender_user_uuid=issuer_user_uuid,
                        content=(
                            f'Ваш уровень в команде "{task.team.name}" повышен до '
                            f"{new_lvl.value}"
                        ),
                    )

                logger.info("Background XP accrual completed for task {}", task_uuid)
            except Exception:
                await session.rollback()
                logger.exception(
                    "Background XP accrual failed for task {}",
                    task_uuid,
                )

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_task(
        cls,
        data: CreateTaskRequest,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> TaskResponse:

        team = await cls._get_team_or_404(data.team_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and team.project.creator_uuid != current_user.uuid
            and team.lead_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления задачей",
            )

        if await UserRepository.get(data.assignee_user_uuid, session) is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        await cls._get_team_member_or_400(
            team.uuid,
            data.assignee_user_uuid,
            session,
        )

        task = Task(
            team_uuid=team.uuid,
            issuer_user_uuid=current_user.uuid,
            assignee_user_uuid=data.assignee_user_uuid,
            title=data.title,
            description=data.description,
            xp_amount=data.xp_amount,
            deadline=data.deadline,
            status=TaskStatus.CREATED,
        )
        session.add(task)
        await session.flush()

        await cls._log_task_action(
            session,
            action="task_created",
            actor_user_uuid=current_user.uuid,
            task_uuid=task.uuid,
            details={
                "team_uuid": str(task.team_uuid),
                "assignee_user_uuid": str(task.assignee_user_uuid),
            },
        )

        await session.commit()
        created_task = await cls._get_task_or_404(task.uuid, session)

        NotificationService.schedule(
            background_tasks,
            recipient_user_uuids=[data.assignee_user_uuid],
            sender_user_uuid=current_user.uuid,
            content=f'Вам назначена новая задача "{data.title}" в команде "{team.name}"',
        )

        return cls._serialize_task(created_task)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_tasks(
        cls,
        current_user: User,
        filters: TaskFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[TaskResponse]:

        if current_user.role == UserRole.ADMIN:
            tasks = await TaskRepository.get_all(filters, session)
        else:
            tasks = await TaskRepository.get_accessible_for_user(
                current_user.uuid,
                filters,
                session,
            )

        return [cls._serialize_task(task) for task in tasks]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_task_by_id(
        cls,
        task_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> TaskResponse:

        task = await cls._get_task_or_404(task_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and task.team.project.creator_uuid != current_user.uuid
            and task.team.lead_uuid != current_user.uuid
            and task.assignee_user_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра задачи",
            )

        return cls._serialize_task(task)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_task(
        cls,
        task_uuid: UUID,
        data: UpdateTaskRequest,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> TaskResponse:

        task = await cls._get_task_or_404(task_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and task.team.project.creator_uuid != current_user.uuid
            and task.team.lead_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления задачей",
            )

        if task.status == TaskStatus.DONE:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Закрытую задачу нельзя изменить",
            )

        changed_fields: list[str] = []
        update_data: dict[str, object | None] = {}
        notify_new_assignee = False

        if "title" in data.model_fields_set and data.title is not None and data.title != task.title:
            update_data["title"] = data.title
            changed_fields.append("title")

        if "description" in data.model_fields_set and data.description != task.description:
            update_data["description"] = data.description
            changed_fields.append("description")

        if "xp_amount" in data.model_fields_set and data.xp_amount is not None and data.xp_amount != task.xp_amount:
            update_data["xp_amount"] = data.xp_amount
            changed_fields.append("xp_amount")

        if "deadline" in data.model_fields_set and data.deadline != task.deadline:
            update_data["deadline"] = data.deadline
            changed_fields.append("deadline")

        if (
            "assignee_user_uuid" in data.model_fields_set
            and data.assignee_user_uuid is not None
            and data.assignee_user_uuid != task.assignee_user_uuid
        ):
            if await UserRepository.get(data.assignee_user_uuid, session) is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден",
                )

            await cls._get_team_member_or_400(
                task.team_uuid,
                data.assignee_user_uuid,
                session,
            )

            update_data["assignee_user_uuid"] = data.assignee_user_uuid
            update_data["status"] = TaskStatus.CREATED
            update_data["accepted_at"] = None
            update_data["submitted_for_review_at"] = None
            update_data["completed_at"] = None
            update_data["review_comment"] = None
            changed_fields.append("assignee_user_uuid")
            notify_new_assignee = True

        if not changed_fields:
            return cls._serialize_task(task)

        await cls._log_task_action(
            session,
            action="task_updated",
            actor_user_uuid=current_user.uuid,
            task_uuid=task.uuid,
            details={"changed_fields": changed_fields},
        )

        updated_task = await TaskRepository.update(
            task,
            TaskRepositoryUpdatePayload(**update_data),
            session,
        )

        if notify_new_assignee and updated_task.assignee_user_uuid is not None:
            NotificationService.schedule(
                background_tasks,
                recipient_user_uuids=[updated_task.assignee_user_uuid],
                sender_user_uuid=current_user.uuid,
                content=(
                    f'Вам назначена новая задача "{updated_task.title}" '
                    f'в команде "{updated_task.team.name}"'
                ),
            )

        return cls._serialize_task(updated_task)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def accept_task(
        cls,
        task_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> TaskResponse:

        task = await cls._get_task_or_404(task_uuid, session)

        if task.assignee_user_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Принять задачу может только назначенный исполнитель",
            )

        if task.status != TaskStatus.CREATED:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Принять можно только новую задачу",
            )

        await cls._log_task_action(
            session,
            action="task_accepted",
            actor_user_uuid=current_user.uuid,
            task_uuid=task.uuid,
        )

        updated_task = await TaskRepository.update(
            task,
            TaskRepositoryUpdatePayload(
                status=TaskStatus.IN_WORK,
                accepted_at=dt.datetime.now(dt.UTC),
                review_comment=None,
            ),
            session,
        )

        return cls._serialize_task(updated_task)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def submit_for_review(
        cls,
        task_uuid: UUID,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> TaskResponse:

        task = await cls._get_task_or_404(task_uuid, session)

        if task.assignee_user_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Отправить задачу на проверку может только исполнитель",
            )

        if task.status != TaskStatus.IN_WORK:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="На проверку можно отправить только задачу в работе",
            )

        await cls._log_task_action(
            session,
            action="task_submitted_for_review",
            actor_user_uuid=current_user.uuid,
            task_uuid=task.uuid,
        )

        updated_task = await TaskRepository.update(
            task,
            TaskRepositoryUpdatePayload(
                status=TaskStatus.ON_CHECK,
                submitted_for_review_at=dt.datetime.now(dt.UTC),
            ),
            session,
        )

        recipient_user_uuids: list[UUID] = []
        if updated_task.team.lead_uuid is not None:
            recipient_user_uuids.append(updated_task.team.lead_uuid)
        if updated_task.team.project.creator_uuid not in recipient_user_uuids:
            recipient_user_uuids.append(updated_task.team.project.creator_uuid)

        assignee_name = (
            updated_task.assignee_user.fio
            if updated_task.assignee_user is not None
            else "исполнителем"
        )
        NotificationService.schedule(
            background_tasks,
            recipient_user_uuids=recipient_user_uuids,
            sender_user_uuid=current_user.uuid,
            content=(
                f'Задача "{updated_task.title}" отправлена на проверку '
                f"пользователем {assignee_name}"
            ),
        )

        return cls._serialize_task(updated_task)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def approve_task(
        cls,
        task_uuid: UUID,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> TaskResponse:

        task = await cls._get_task_or_404(task_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and task.team.project.creator_uuid != current_user.uuid
            and task.team.lead_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления задачей",
            )

        if task.status != TaskStatus.ON_CHECK:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Подтвердить можно только задачу на проверке",
            )

        await cls._log_task_action(
            session,
            action="task_approved",
            actor_user_uuid=current_user.uuid,
            task_uuid=task.uuid,
            details={"assignee_user_uuid": str(task.assignee_user_uuid)},
        )

        approved_task = await TaskRepository.update(
            task,
            TaskRepositoryUpdatePayload(
                status=TaskStatus.DONE,
                completed_at=dt.datetime.now(dt.UTC),
                review_comment=None,
            ),
            session,
        )

        if background_tasks is not None:
            background_tasks.add_task(
                cls.process_task_xp_accrual,
                task_uuid,
                current_user.uuid,
            )

        if approved_task.assignee_user_uuid is not None:
            NotificationService.schedule(
                background_tasks,
                recipient_user_uuids=[approved_task.assignee_user_uuid],
                sender_user_uuid=current_user.uuid,
                content=f'Задача "{approved_task.title}" подтверждена и закрыта',
            )

        return cls._serialize_task(approved_task)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def reject_task(
        cls,
        task_uuid: UUID,
        data: RejectTaskRequest,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> TaskResponse:

        task = await cls._get_task_or_404(task_uuid, session)

        if (
            current_user.role != UserRole.ADMIN
            and task.team.project.creator_uuid != current_user.uuid
            and task.team.lead_uuid != current_user.uuid
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для управления задачей",
            )

        if task.status != TaskStatus.ON_CHECK:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Отклонить можно только задачу на проверке",
            )

        await cls._log_task_action(
            session,
            action="task_rejected",
            actor_user_uuid=current_user.uuid,
            task_uuid=task.uuid,
            details={"review_comment": data.review_comment},
        )

        rejected_task = await TaskRepository.update(
            task,
            TaskRepositoryUpdatePayload(
                status=TaskStatus.IN_WORK,
                submitted_for_review_at=None,
                completed_at=None,
                review_comment=data.review_comment,
            ),
            session,
        )

        if rejected_task.assignee_user_uuid is not None:
            NotificationService.schedule(
                background_tasks,
                recipient_user_uuids=[rejected_task.assignee_user_uuid],
                sender_user_uuid=current_user.uuid,
                content=(
                    f'Задача "{rejected_task.title}" отклонена с комментарием: '
                    f"{rejected_task.review_comment}"
                    if rejected_task.review_comment
                    else f'Задача "{rejected_task.title}" отклонена и возвращена в работу'
                ),
            )

        return cls._serialize_task(rejected_task)
