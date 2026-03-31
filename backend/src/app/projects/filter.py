from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, Field


class ProjectFilterQueryParams(BaseModel):

    creator_uuid: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    limit: int | None = Field(default=None, ge=1, le=1000)
    cursor: UUID | None = None


ProjectFilterDepends = Annotated[ProjectFilterQueryParams, Depends()]
