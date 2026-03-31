from collections.abc import Awaitable, Callable
from functools import wraps

from fastapi import HTTPException, status
from loguru import logger

from app.error_handler.constant import (
    DB_CONNECTION_ERRORS,
    DB_CONNECTION_ERROR_MESSAGE,
)


def handle_connection_errors[**P, R](
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:

        try:
            return await func(*args, **kwargs)
        except DB_CONNECTION_ERRORS as e:

            logger.exception(DB_CONNECTION_ERROR_MESSAGE)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=DB_CONNECTION_ERROR_MESSAGE,
            ) from e

    return wrapper
