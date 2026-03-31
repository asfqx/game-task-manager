from collections.abc import Awaitable, Callable
from functools import wraps

from fastapi import HTTPException, status
from loguru import logger

from app.error_handler.constant import DB_MODEL_ERRORS, DB_MODEL_ERROR_MESSAGE


def handle_model_errors[**P, R](
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:

        try:
            return await func(*args, **kwargs)
        except DB_MODEL_ERRORS as e:

            logger.exception(DB_MODEL_ERROR_MESSAGE)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=DB_MODEL_ERROR_MESSAGE,
            ) from e

    return wrapper
