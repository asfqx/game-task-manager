from fastapi import APIRouter, BackgroundTasks, status
from pydantic import EmailStr

from app.adapters.cache import get_cache_adapter
from app.adapters.cache.adapters import BaseCacheAdapter
from app.auth.query_param import TokenQueryParam
from app.auth.schemas import PasswordResetConfirmRequest
from app.auth.services import PasswordResetService
from app.core import DBSession, RateLimitErrorResponse
from app.error_handler import error_schemas


router = APIRouter(prefix="/password-reset")


cache: BaseCacheAdapter = get_cache_adapter()


@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Запросить сброс пароля",
    description=(
        "Отправляет пользователю письмо с токеном для сброса пароля."
    ),
    responses={
        202: {
            "description": "Запрос на сброс пароля успешно принят",
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
async def password_reset(
    email: EmailStr,
    background: BackgroundTasks,
    session: DBSession,
) -> None:
    await PasswordResetService.reset(email, background, session)


@router.post(
    "/confirm",
    status_code=status.HTTP_200_OK,
    summary="Подтвердить сброс пароля",
    description=(
        "Подтверждает токен сброса пароля и устанавливает новый пароль для пользователя."
    ),
    responses={
        200: {
            "description": "Пароль успешно обновлен",
        },
        400: {
            "description": "Токен сброса некорректен или просрочен",
            "model": error_schemas.BadRequestErrorResponse,
        },
        404: {
            "description": "Пользователь не найден",
            "model": error_schemas.NotFoundErrorResponse,
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "model": error_schemas.InternalServerErrorResponse,
        },
    },
)
async def password_reset_confirm(
    data: PasswordResetConfirmRequest,
    token: TokenQueryParam,
    session: DBSession,
) -> None:
    await PasswordResetService.confirm(data.email, token, data.new_password, session)
