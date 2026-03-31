from http import HTTPStatus
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RateLimitErrorResponse(BaseModel):

    code: Literal[HTTPStatus.TOO_MANY_REQUESTS]

    retry_after_seconds: int | None

    model_config = ConfigDict(
        from_attributes=True,
    )
