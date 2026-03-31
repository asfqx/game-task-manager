from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.lvls.schema import LvlSummaryResponse
from app.users.schema import UserShortResponse


class CreateTeamRequest(BaseModel):

    project_uuid: UUID
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    lead_uuid: UUID | None = None
    member_uuids: list[UUID] = Field(default_factory=list)


class UpdateTeamRequest(BaseModel):

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    lead_uuid: UUID | None = None


class AddTeamMemberRequest(BaseModel):

    user_uuid: UUID


class TeamProjectResponse(BaseModel):

    uuid: UUID
    title: str


class TeamMemberResponse(BaseModel):

    uuid: UUID
    user_uuid: UUID
    user: UserShortResponse | None = None
    added_by_uuid: UUID | None = None
    added_by: UserShortResponse | None = None
    lvl_uuid: UUID | None = None
    lvl: LvlSummaryResponse | None = None
    xp_amount: int
    joined_at: datetime
    is_team_lead: bool


class TeamResponse(BaseModel):

    uuid: UUID
    project_uuid: UUID
    project: TeamProjectResponse
    name: str
    description: str | None = None
    lead_uuid: UUID | None = None
    lead: UserShortResponse | None = None
    created_by_uuid: UUID | None = None
    created_by: UserShortResponse | None = None
    members_count: int
    members: list[TeamMemberResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
