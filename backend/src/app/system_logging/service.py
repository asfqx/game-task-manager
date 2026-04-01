from collections.abc import Sequence
from uuid import UUID
from typing import Any

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
from app.system_logging.model import XpAccrualLog
from app.users.model import User


class SystemLoggingService:

    @staticmethod
    async def log_user_action(
        session: AsyncSession,
        *,
        action: str,
        actor_user_uuid: UUID | None,
        entity_type: str | None = None,
        entity_uuid: UUID | None = None,
        details: dict[str, Any] | None = None,
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
    ) -> Sequence[XpAccrualLog]:

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

        return logs

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_user_action_logs(
        cls,
        current_user: User,
        filters: UserActionLogFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[UserActionLog]:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Журнал действий пользователей доступен только администратору",
            )

        logs = await UserActionLogRepository.get_all(filters, session)

        return logs
