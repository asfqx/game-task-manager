from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, Field

from app.enum import TaskStatus


class TaskFilterQueryParams(BaseModel):

    team_uuid: UUID | None = None
    issuer_user_uuid: UUID | None = None
    assignee_user_uuid: UUID | None = None
    status: TaskStatus | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)
    cursor: UUID | None = None


TaskFilterDepends = Annotated[TaskFilterQueryParams, Depends()]
