import datetime as dt
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.constant import ALGORITHM
from app.core import AsyncSessionLocal, DBSession, settings
from app.enum import UserRole, UserStatus
from app.users.model import User
from app.users.repository import UserRepository


security = HTTPBearer(bearerFormat="JWT", scheme_name="Authorization")


async def resolve_user_by_token(
    token: str,
    session: AsyncSession,
) -> User:

    try:
        payload = jwt.decode(
            token,
            settings.hash_secret_key,
            algorithms=[ALGORITHM],
        )
    except JWTError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Зарегистрируйтесь или войдите, чтобы продолжить",
        ) from error

    raw_user_uuid = payload.get("sub")

    if raw_user_uuid is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Переданный токен неверный или истек",
        )

    try:
        user_uuid = UUID(str(raw_user_uuid))
    except ValueError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Переданный токен неверный или истек",
        ) from error

    exp = payload.get("exp")

    if exp is None or dt.datetime.now(dt.UTC).timestamp() > float(exp):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Переданный токен истек",
        )

    user = await UserRepository.get(user_uuid, session)

    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    return user


async def get_current_user(
    session: DBSession,
    token_credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:

    return await resolve_user_by_token(
        token_credentials.credentials,
        session,
    )


UserDepends = Depends(get_current_user)
AuthenticatedUser = Annotated[User, UserDepends]


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован",
        )

    return user


ActiveUserDepends = Depends(get_current_active_user)
AuthenticatedActiveUser = Annotated[User, ActiveUserDepends]


async def get_current_active_user_for_stream(
    token_credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:

    async with AsyncSessionLocal() as session:
        user = await resolve_user_by_token(
            token_credentials.credentials,
            session,
        )

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Пользователь заблокирован",
            )

        return user


ActiveStreamUserDepends = Depends(get_current_active_user_for_stream)
AuthenticatedActiveStreamUser = Annotated[User, ActiveStreamUserDepends]


def get_current_user_by_role(*allowed_roles: UserRole):

    async def dependency(
        user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:

        if user.role not in allowed_roles:
            allowed_roles_label = ", ".join(role.value for role in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {allowed_roles_label}",
            )

        return user

    return dependency


get_current_admin = get_current_user_by_role(UserRole.ADMIN)

AdminUser = Depends(get_current_admin)
AuthenticatedAdminUser = Annotated[User, AdminUser]
