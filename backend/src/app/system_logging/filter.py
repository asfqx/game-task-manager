from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, Field


class XpAccrualLogFilterQueryParams(BaseModel):

    recipient_user_uuid: UUID | None = None
    issuer_user_uuid: UUID | None = None
    task_uuid: UUID | None = None
    team_uuid: UUID | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)
    cursor: UUID | None = None


XpAccrualLogFilterDepends = Annotated[XpAccrualLogFilterQueryParams, Depends()]


class UserActionLogFilterQueryParams(BaseModel):

    actor_user_uuid: UUID | None = None
    action: str | None = Field(default=None, min_length=1, max_length=100)
    entity_type: str | None = Field(default=None, min_length=1, max_length=100)
    entity_uuid: UUID | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)
    cursor: UUID | None = None


UserActionLogFilterDepends = Annotated[UserActionLogFilterQueryParams, Depends()]
