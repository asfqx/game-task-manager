from fastapi import APIRouter, BackgroundTasks, Request, Response, status

from app.auth.schemas import (
    CreateLoginRequest,
    CreateRegisterRequest,
    TokenPairResponse,
)
from app.auth.services import AuthMailService, AuthService
from app.core import DBSession, RateLimitErrorResponse
from app.error_handler import error_schemas
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description=(
        "Создает нового пользователя с указанными email, username, ФИО, ролью и паролем. "
        "После успешной регистрации отправляется приветственное письмо и письмо для подтверждения email."
    ),
    responses={
        201: {
            "description": "Пользователь успешно зарегистрирован",
        },
        409: {
            "description": "Пользователь с таким email или username уже существует",
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
async def register(
    background: BackgroundTasks,
    register_data: CreateRegisterRequest,
    session: DBSession,
) -> None:
    await AuthService.register_user(
        email=register_data.email,
        username=register_data.username,
        password=register_data.password,
        role=register_data.role,
        fio=register_data.fio,
        background=background,
        session=session,
    )

    background.add_task(
        AuthMailService.send_welcome_mail,
        register_data.email,
        register_data.username,
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Аутентификация пользователя",
    description=(
        "Авторизует пользователя по логину и паролю, возвращает access и refresh токены. "
        "Если учетные данные некорректны или почта не подтверждена, возвращается ошибка."
    ),
    response_model=TokenPairResponse,
    responses={
        200: {
            "description": "Вход выполнен успешно",
            "model": TokenPairResponse,
        },
        401: {
            "description": "Неверный пароль или почта не подтверждена",
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
async def login(
    response: Response,
    login_data: CreateLoginRequest,
    session: DBSession,
) -> TokenPairResponse:
    return await AuthService.login_user(
        login=login_data.login,
        password=login_data.password,
        response=response,
        session=session,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Выход пользователя из системы",
    description=(
        "Завершает текущую сессию пользователя и отзывает refresh токен. "
        "Требуется JWT access-токен в заголовке Authorization."
    ),
    responses={
        202: {
            "description": "Выход выполнен успешно",
        },
        400: {
            "description": "Некорректный запрос на выход",
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
async def logout(
    user: AuthenticatedActiveUser,
    request: Request,
    response: Response,
    session: DBSession,
) -> None:
    await AuthService.logout(user, request, response, session)
