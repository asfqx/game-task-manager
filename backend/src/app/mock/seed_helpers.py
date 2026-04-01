from pydantic import BaseModel

from app.auth.schemas.auth import CreateSuperuserRequest
from app.enum import UserRole, UserStatus
from app.security import Argon2Hasher
from app.users.model import User
from app.users.repository import UserRepository


SUPERUSER_DATA = CreateSuperuserRequest(
    email="root@example.com",
    username="rootadmin",
    password="strongpass123",
    fio="Root Admin",
)


class SeedUserUpdatePayload(BaseModel):
    username: str
    fio: str
    role: UserRole
    status: UserStatus
    email_confirmed: bool


async def ensure_seed_user(
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
        return await UserRepository.create(
            User(
                email=email,
                username=username,
                fio=fio,
                role=role,
                password_hash=Argon2Hasher.hash(password),
                email_confirmed=email_confirmed,
                status=UserStatus.ACTIVE,
            ),
            session=session,
        )

    user = await UserRepository.update(
        user,
        SeedUserUpdatePayload(
            username=username,
            fio=fio,
            role=role,
            status=UserStatus.ACTIVE,
            email_confirmed=email_confirmed,
        ),
        session=session,
    )

    if not Argon2Hasher.verify(password, user.password_hash):
        await UserRepository.update_password(
            user,
            Argon2Hasher.hash(password),
            session=session,
        )
        refreshed_user = await UserRepository.get(user.uuid, session=session)
        if refreshed_user is not None:
            user = refreshed_user

    return user
