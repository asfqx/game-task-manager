from loguru import logger
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.auth.services import AuthService
from app.core import AsyncSessionLocal
from app.enum import UserRole, UserStatus
from app.security import Argon2Hasher
from app.users.repository import UserRepository

from .demo_workspace import seed_demo_workspace
from .seed_helpers import SUPERUSER_DATA


class SuperuserUpdatePayload(BaseModel):
    email_confirmed: bool
    role: UserRole
    status: UserStatus


async def bootstrap_mock_data() -> None:
    async with AsyncSessionLocal() as session:
        existing_user = await UserRepository.get_by_login(
            SUPERUSER_DATA.email,
            session=session,
        )

        if existing_user is None:
            try:
                await AuthService.create_superuser(data=SUPERUSER_DATA, session=session)
                logger.success(
                    "Суперпользователь создан успешно: email={}, username={}",
                    SUPERUSER_DATA.email,
                    SUPERUSER_DATA.username,
                )
            except IntegrityError:
                await session.rollback()
                logger.error("Ошибка БД при создании суперпользователя (возможно, дублирование)")
        else:
            if not Argon2Hasher.verify(
                SUPERUSER_DATA.password,
                existing_user.password_hash,
            ):
                await UserRepository.update_password(
                    existing_user,
                    Argon2Hasher.hash(SUPERUSER_DATA.password),
                    session=session,
                )
                refreshed_user = await UserRepository.get(existing_user.uuid, session=session)
                if refreshed_user is not None:
                    existing_user = refreshed_user

            await UserRepository.update(
                existing_user,
                SuperuserUpdatePayload(
                    email_confirmed=True,
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                ),
                session=session,
            )
            logger.info("Суперпользователь уже существует")

        owner = await UserRepository.get_by_login(SUPERUSER_DATA.email, session=session)

    if owner is not None:
        await seed_demo_workspace(owner)
