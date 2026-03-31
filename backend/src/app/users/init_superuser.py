from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.auth.schemas.auth import CreateSuperuserRequest
from app.core import AsyncSessionLocal
from app.users.repository import UserRepository


async def create_first_superuser() -> None:
    from app.auth.services import AuthService

    register_data = CreateSuperuserRequest(
        email="root@example.com",
        username="root",
        password="strong_password",
        fio="roooot",
    )

    async with AsyncSessionLocal() as session:
        existing_user = await UserRepository.get_by_login(
            register_data.email,
            session=session,
        )
        if existing_user:
            logger.info("Суперпользователь уже существует")
            return

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
