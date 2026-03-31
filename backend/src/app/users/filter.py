from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field

from app.enum import UserRole, UserStatus, Gender


class UserFilterQueryParams(BaseModel):

    username: str | None = None
    email: str | None = None
    fio: str | None = None
    gender: Gender | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)


UserFilterDepends = Annotated[UserFilterQueryParams, Depends()]
