from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.users.schema import UserShortResponse


class CreateProjectRequest(BaseModel):

    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class UpdateProjectRequest(BaseModel):

    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class ProjectTeamSummaryResponse(BaseModel):

    uuid: UUID
    name: str
    description: str | None = None
    lead_uuid: UUID | None = None
    lead_name: str | None = None
    members_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):

    uuid: UUID
    title: str
    description: str | None = None
    creator_uuid: UUID
    creator: UserShortResponse | None = None
    teams_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):

    teams: list[ProjectTeamSummaryResponse] = Field(default_factory=list)
