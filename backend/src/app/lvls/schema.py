from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateLvlRequest(BaseModel):

    value: str = Field(min_length=1, max_length=255)
    required_xp: int = Field(ge=0)


class UpdateLvlRequest(BaseModel):

    value: str | None = Field(default=None, min_length=1, max_length=255)
    required_xp: int | None = Field(default=None, ge=0)


class LvlSummaryResponse(BaseModel):

    uuid: UUID
    value: str
    required_xp: int


class LvlResponse(LvlSummaryResponse):

    created_at: datetime
    updated_at: datetime
