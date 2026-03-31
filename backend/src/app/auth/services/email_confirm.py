import secrets

from fastapi import BackgroundTasks, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.cache import get_cache_adapter
from app.adapters.cache.adapters import BaseCacheAdapter
from app.system_logging.service import SystemLoggingService
from app.users.repository import UserRepository
from app.auth.constant import EMAIL_CONFIRM_TOKEN_EXPIRE_TIME

from .auth_mail import AuthMailService


class EmailConfirmService:

    @staticmethod
    async def send_token(
        email: str,
        background: BackgroundTasks,
        session: AsyncSession,
    ) -> None:
        
        email = email.lower()

        cache: BaseCacheAdapter = get_cache_adapter()

        user = await UserRepository.get_by_login(email, session)

        if user:
            if user.email_confirmed:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Почта уже подтверждена",
                )
            
            token = secrets.token_urlsafe(6)

            await cache.set(
                f'email-confirm:{email}',
                token,
                EMAIL_CONFIRM_TOKEN_EXPIRE_TIME,
            )

            background.add_task(
                AuthMailService.send_email_confirm,
                email,
                user.username,
                token,
            )

    @staticmethod
    async def confirm_token(
        email: str,
        token: str,
        session: AsyncSession,
    ):
        
        email = email.lower()

        cache: BaseCacheAdapter = get_cache_adapter()
        
        stored_token = await cache.get(f"email-confirm:{email}")

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
        
        if user.email_confirmed:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Почта уже подтверждена",
            )

        await UserRepository.update_email_confirm(
            user,
            session,
        )
        await SystemLoggingService.log_user_action(
            session,
            action="email_confirmed",
            actor_user_uuid=user.uuid,
            entity_type="user",
            entity_uuid=user.uuid,
        )

    
