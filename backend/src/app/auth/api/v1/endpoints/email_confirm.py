from fastapi import APIRouter, BackgroundTasks, status
from pydantic import EmailStr

from app.auth.query_param import TokenQueryParam
from app.auth.schemas import EmailConfirmRequest
from app.auth.services import EmailConfirmService
from app.core import DBSession, RateLimitErrorResponse
from app.error_handler import error_schemas


router = APIRouter(prefix="/email-confirm")


@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Запросить подтверждение email",
    description=(
        "Отправляет письмо с токеном для подтверждения электронной почты пользователя."
    ),
    responses={
        202: {
            "description": "Запрос на подтверждение почты успешно принят",
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
async def email_confirm_request(
    email: EmailStr,
    background: BackgroundTasks,
    session: DBSession,
) -> None:
    await EmailConfirmService.send_token(email, background, session)


@router.post(
    "/confirm",
    status_code=status.HTTP_200_OK,
    summary="Подтвердить email",
    description=(
        "Подтверждает адрес электронной почты по токену, полученному пользователем на email."
    ),
    responses={
        200: {
            "description": "Почта успешно подтверждена",
        },
        400: {
            "description": "Токен подтверждения некорректен или просрочен",
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
async def email_confirm(
    data: EmailConfirmRequest,
    token: TokenQueryParam,
    session: DBSession,
) -> None:
    await EmailConfirmService.confirm_token(data.email, token, session)
