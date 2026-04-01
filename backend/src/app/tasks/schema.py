from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enum import TaskStatus
from app.lvls.schema import LvlSummaryResponse
from app.users.schema import UserShortResponse


class CreateTaskRequest(BaseModel):

    team_uuid: UUID
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    assignee_user_uuid: UUID
    xp_amount: int = Field(ge=0)
    deadline: datetime | None = None


class UpdateTaskRequest(BaseModel):

    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    assignee_user_uuid: UUID | None = None
    xp_amount: int | None = Field(default=None, ge=0)
    deadline: datetime | None = None


class RejectTaskRequest(BaseModel):

    review_comment: str = Field(min_length=1, max_length=4000)


class TaskTeamResponse(BaseModel):

    uuid: UUID
    name: str
    project_uuid: UUID
    project_title: str

    model_config = ConfigDict(from_attributes=True)


class TaskAssigneeProgressResponse(BaseModel):

    xp_amount: int
    lvl_uuid: UUID | None = None
    lvl: LvlSummaryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):

    uuid: UUID
    team_uuid: UUID
    team: TaskTeamResponse
    issuer_user_uuid: UUID | None = None
    issuer_user: UserShortResponse | None = None
    assignee_user_uuid: UUID | None = None
    assignee_user: UserShortResponse | None = None
    title: str
    description: str | None = None
    review_comment: str | None = None
    xp_amount: int
    status: TaskStatus
    deadline: datetime | None = None
    accepted_at: datetime | None = None
    submitted_for_review_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    assignee_team_progress: TaskAssigneeProgressResponse | None = None

    model_config = ConfigDict(from_attributes=True)
