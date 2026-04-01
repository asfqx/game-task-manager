from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core import DBSession, RateLimitErrorResponse
from app.error_handler import error_schemas
from app.users.dependency import AuthenticatedActiveUser
from app.users.filter import UserFilterDepends
from app.users.schema import (
    CreatePreSignedURLResponse,
    GetUserProfileResponse,
    UpdateUserProfileRequest,
    UpdateUserProfileResponse,
    UserShortResponse,
)
from app.users.service import UserService


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Получить список пользователей",
    description="Возвращает список пользователей. Доступно только администратору.",
    response_model=list[GetUserProfileResponse],
)
async def get_all_users(
    user: AuthenticatedActiveUser,
    filters: UserFilterDepends,
    session: DBSession,
) -> Sequence[GetUserProfileResponse]:
    return await UserService.get_all(current_user=user, filters=filters, session=session)


@router.get(
    "/me/",
    status_code=status.HTTP_200_OK,
    summary="Получить мой профиль",
    description=(
        "Возвращает профиль текущего авторизованного пользователя. "
        "Требуется JWT access-токен в заголовке Authorization."
    ),
    response_model=GetUserProfileResponse,
    responses={
        200: {
            "description": "Профиль пользователя успешно получен",
            "model": GetUserProfileResponse,
        },
        401: {
            "description": "Пользователь не авторизован",
            "model": error_schemas.UnauthorizedErrorResponse,
        },
        404: {
            "description": "Пользователь не найден",
            "model": error_schemas.NotFoundErrorResponse,
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitErrorResponse,
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "model": error_schemas.InternalServerErrorResponse,
        },
    },
)
async def get_user_profile(
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> GetUserProfileResponse:
    return await UserService.get_user_profile(
        current_user=user,
        session=session,
    )


@router.patch(
    "/me/",
    status_code=status.HTTP_200_OK,
    summary="Обновить мой профиль",
    description=(
        "Обновляет email, username, ФИО или avatar_url текущего пользователя. "
        "Требуется JWT access-токен в заголовке Authorization."
    ),
    response_model=UpdateUserProfileResponse,
    responses={
        200: {
            "description": "Профиль пользователя успешно обновлен",
            "model": UpdateUserProfileResponse,
        },
        401: {
            "description": "Пользователь не авторизован",
            "model": error_schemas.UnauthorizedErrorResponse,
        },
        404: {
            "description": "Пользователь не найден",
            "model": error_schemas.NotFoundErrorResponse,
        },
        409: {
            "description": "Email или username уже заняты",
            "model": error_schemas.AlreadyExistErrorResponse,
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitErrorResponse,
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "model": error_schemas.InternalServerErrorResponse,
        },
    },
)
async def update_bio(
    new_bio: UpdateUserProfileRequest,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> UpdateUserProfileResponse:
    return await UserService.update_bio(
        new_bio=new_bio,
        current_user=user,
        session=session,
    )


@router.get(
    "/directory",
    status_code=status.HTTP_200_OK,
    summary="Получить каталог пользователей",
    response_model=list[UserShortResponse],
)
async def get_directory(
    user: AuthenticatedActiveUser,
    session: DBSession,
    q: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=20, ge=1, le=100),
) -> Sequence[UserShortResponse]:

    return await UserService.get_directory(
        current_user=user,
        session=session,
        query=q,
        limit=limit,
    )


@router.get(
    "/{user_uuid}",
    status_code=status.HTTP_200_OK,
    summary="Получить профиль пользователя по UUID",
    description="Возвращает профиль пользователя по UUID. Требуется JWT access-токен.",
    response_model=GetUserProfileResponse,
    responses={
        200: {
            "description": "Профиль пользователя успешно получен",
            "model": GetUserProfileResponse,
        },
        401: {
            "description": "Пользователь не авторизован",
            "model": error_schemas.UnauthorizedErrorResponse,
        },
        404: {
            "description": "Пользователь не найден",
            "model": error_schemas.NotFoundErrorResponse,
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitErrorResponse,
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "model": error_schemas.InternalServerErrorResponse,
        },
    },
)
async def get_user_by_uuid(
    user_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> GetUserProfileResponse:
    return await UserService.get_user_by_id(
        user_uuid=user_uuid,
        current_user=user,
        session=session,
    )


@router.delete(
    "/{user_uuid}",
    status_code=status.HTTP_200_OK,
    summary="Заблокировать пользователя",
    description="Блокирует пользователя по UUID. Доступно только администратору.",
)
async def delete_user(
    user_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> None:

    await UserService.delete(current_user=user, user_uuid=user_uuid, session=session)


@router.patch(
    "/{user_uuid}/unban",
    status_code=status.HTTP_200_OK,
    summary="Разблокировать пользователя",
    description="Снимает блокировку с пользователя по UUID. Доступно только администратору.",
)
async def unban_user(
    user_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> None:

    await UserService.unban(current_user=user, user_uuid=user_uuid, session=session)


@router.get(
    "/me/avatar/upload-url",
    status_code=status.HTTP_200_OK,
    summary="Получить ссылку для загрузки аватара",
    description=(
        "Возвращает pre-signed URL для загрузки аватара пользователя в S3-совместимое хранилище. "
        "Требуется JWT access-токен в заголовке Authorization."
    ),
    response_model=CreatePreSignedURLResponse,
    responses={
        200: {
            "description": "Ссылка для загрузки аватара успешно получена",
            "model": CreatePreSignedURLResponse,
        },
        401: {
            "description": "Пользователь не авторизован",
            "model": error_schemas.UnauthorizedErrorResponse,
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitErrorResponse,
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "model": error_schemas.InternalServerErrorResponse,
        },
    },
)
async def upload_avatar(
    user: AuthenticatedActiveUser,
) -> CreatePreSignedURLResponse:

    return await UserService.upload_avatar(user=user)
