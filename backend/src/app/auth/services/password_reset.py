import secrets

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.cache import get_cache_adapter
from app.auth.constant import PASSWORD_RESET_TOKEN_EXPIRE_TIME
from app.security import Argon2Hasher
from app.system_logging.service import SystemLoggingService
from app.users.repository import UserRepository

from .auth_mail import AuthMailService


class PasswordResetService:

    @staticmethod
    async def reset(
        email: str,
        background: BackgroundTasks,
        session: AsyncSession
    ) -> None:

        email = email.lower()

        user = await UserRepository.get_by_login(email, session)

        if user:
            token = secrets.token_urlsafe(8)

            cache_adapter = get_cache_adapter()

            await cache_adapter.set(
                f'password-reset:{email}',
                token,
                PASSWORD_RESET_TOKEN_EXPIRE_TIME,
            )

            background.add_task(
                AuthMailService.send_password_reset_email,
                email,
                user.username,
                token,
            )
            await SystemLoggingService.log_user_action(
                session,
                action="password_reset_requested",
                actor_user_uuid=user.uuid,
                entity_type="user",
                entity_uuid=user.uuid,
            )

    @staticmethod
    async def confirm(
        email: str,
        token: str,
        new_password: str,
        session: AsyncSession
    ) -> None:
        
        email = email.lower()

        cache_adapter = get_cache_adapter()

        stored_token = await cache_adapter.get(f"password-reset:{email}")

        if not stored_token or stored_token != token:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Невалидный или истекший токен",
            )

        user = await UserRepository.get_by_login(email, session)

        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Пользователь не найден",
            )

        await UserRepository.update_password(
            user,
            Argon2Hasher.hash(new_password),
            session,
        )
        await SystemLoggingService.log_user_action(
            session,
            action="password_reset_completed",
            actor_user_uuid=user.uuid,
            entity_type="user",
            entity_uuid=user.uuid,
        )

