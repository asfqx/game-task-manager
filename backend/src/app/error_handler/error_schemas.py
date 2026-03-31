from http import HTTPStatus
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BaseErrorModel(BaseModel):

    detail: str


class BadRequestErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.BAD_REQUEST]

    model_config = ConfigDict(
        from_attributes=True,
    )


class UnauthorizedErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.UNAUTHORIZED]

    model_config = ConfigDict(
        from_attributes=True,
    )


class NotFoundErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.NOT_FOUND]



class AlreadyExistErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.CONFLICT]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ConflictErrorResponse(AlreadyExistErrorResponse):

    code: Literal[HTTPStatus.CONFLICT]


class InternalServerErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.INTERNAL_SERVER_ERROR]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ForbiddenErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.FORBIDDEN]

    model_config = ConfigDict(
        from_attributes=True,
    )


class GoneErrorResponse(BaseErrorModel):

    code: Literal[HTTPStatus.GONE]

    model_config = ConfigDict(
        from_attributes=True,
    )

