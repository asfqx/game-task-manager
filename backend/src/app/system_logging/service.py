from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.system_logging.filter import (
    UserActionLogFilterQueryParams,
    XpAccrualLogFilterQueryParams,
)
from app.system_logging.model import UserActionLog
from app.system_logging.repository import UserActionLogRepository, XpAccrualLogRepository
from app.system_logging.schema import (
    UserActionLogResponse,
    XpAccrualLogResponse,
    XpAccrualLogTaskResponse,
)
from app.system_logging.type import UserActionLogDetailsPayload
from app.users.model import User
from app.users.schema import UserShortResponse


class SystemLoggingService:

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
    async def log_user_action(
        session: AsyncSession,
        *,
        action: str,
        actor_user_uuid: UUID | None,
        entity_type: str | None = None,
        entity_uuid: UUID | None = None,
        details: UserActionLogDetailsPayload | None = None,
        commit: bool = True,
    ) -> None:

        await UserActionLogRepository.create(
            UserActionLog(
                actor_user_uuid=actor_user_uuid,
                action=action,
                entity_type=entity_type,
                entity_uuid=entity_uuid,
                details=details,
            ),
            session,
        )

        if commit:
            await session.commit()

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_xp_logs(
        cls,
        current_user: User,
        filters: XpAccrualLogFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[XpAccrualLogResponse]:

        logs = await XpAccrualLogRepository.get_all(filters, session)

        if current_user.role != UserRole.ADMIN:
            logs = [
                log
                for log in logs
                if log.recipient_user_uuid == current_user.uuid
                or log.issuer_user_uuid == current_user.uuid
                or (
                    log.task is not None
                    and (
                        log.task.team.project.creator_uuid == current_user.uuid
                        or log.task.team.lead_uuid == current_user.uuid
                    )
                )
            ]

        return [
            XpAccrualLogResponse(
                uuid=log.uuid,
                issued_at=log.issued_at,
                xp_amount=log.xp_amount,
                recipient_user_uuid=log.recipient_user_uuid,
                recipient_user=cls._serialize_user(log.recipient_user),
                issuer_user_uuid=log.issuer_user_uuid,
                issuer_user=cls._serialize_user(log.issuer_user),
                task_uuid=log.task_uuid,
                task=(
                    XpAccrualLogTaskResponse(
                        uuid=log.task.uuid,
                        title=log.task.title,
                        team_uuid=log.task.team.uuid,
                        team_name=log.task.team.name,
                        project_uuid=log.task.team.project.uuid,
                        project_title=log.task.team.project.title,
                    )
                    if log.task is not None
                    else None
                ),
            )
            for log in logs
        ]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_user_action_logs(
        cls,
        current_user: User,
        filters: UserActionLogFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[UserActionLogResponse]:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Журнал действий пользователей доступен только администратору",
            )

        logs = await UserActionLogRepository.get_all(filters, session)

        return [
            UserActionLogResponse(
                uuid=log.uuid,
                issued_at=log.issued_at,
                actor_user_uuid=log.actor_user_uuid,
                actor_user=cls._serialize_user(log.actor_user),
                action=log.action,
                entity_type=log.entity_type,
                entity_uuid=log.entity_uuid,
                details=log.details,
            )
            for log in logs
        ]
