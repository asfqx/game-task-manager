from fastapi import APIRouter, Response, status

from app.auth.schemas import (
    CreateTokenPairResponse,
    GetAccessTokenRequest,
    GetUserRoleResponse,
    TokenPairResponse,
)
from app.auth.services import AuthService
from app.core import DBSession, RateLimitErrorResponse
from app.error_handler import error_schemas
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновить токены доступа",
    description=(
        "Обновляет access и refresh токены по действующему refresh_token. "
        "Refresh токен передается в теле запроса."
    ),
    response_model=TokenPairResponse,
    responses={
        200: {
            "description": "Токены успешно обновлены",
            "model": TokenPairResponse,
        },
        400: {
            "description": "Некорректный запрос на обновление токенов",
            "model": error_schemas.BadRequestErrorResponse,
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
async def refresh_token(
    refresh_data: CreateTokenPairResponse,
    user: AuthenticatedActiveUser,
    response: Response,
    session: DBSession,
) -> TokenPairResponse:
    return await AuthService.refresh_token(
        refresh_data.refresh_token,
        user,
        response,
        session,
    )


@router.post(
    "/check_role",
    status_code=status.HTTP_200_OK,
    summary="Проверить роль пользователя по токену",
    description=(
        "Проверяет access-токен и возвращает роль пользователя, которой он принадлежит."
    ),
    response_model=GetUserRoleResponse,
    responses={
        200: {
            "description": "Роль пользователя успешно определена",
            "model": GetUserRoleResponse,
        },
        400: {
            "description": "Передан невалидный или просроченный access-токен",
            "model": error_schemas.BadRequestErrorResponse,
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
async def check_role(
    access_data: GetAccessTokenRequest,
    session: DBSession,
) -> GetUserRoleResponse:
    return await AuthService.get_role_from_jwt(access_data.access_token, session)
