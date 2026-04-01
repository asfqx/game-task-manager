from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enum import Gender
from app.lvls.schema import LvlSummaryResponse


class UserShortResponse(BaseModel):

    uuid: UUID
    username: str
    fio: str

    model_config = ConfigDict(from_attributes=True)


class UserTeamSummaryResponse(BaseModel):

    team_uuid: UUID
    team_name: str
    project_uuid: UUID
    project_title: str
    is_team_lead: bool
    xp_amount: int
    lvl_uuid: UUID | None = None
    lvl: LvlSummaryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCompletedTaskResponse(BaseModel):

    task_uuid: UUID
    title: str
    team_uuid: UUID
    team_name: str
    project_uuid: UUID
    project_title: str
    xp_amount: int
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class GetUserProfileResponse(BaseModel):

    uuid: UUID
    email: EmailStr
    username: str
    fio: str
    role: str
    status: str
    gender: Gender | None = None
    email_confirmed: bool = False
    avatar_url: str | None = None
    telegram: str | None = None
    phone_number: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None
    teams: list[UserTeamSummaryResponse] = Field(default_factory=list)
    completed_tasks: list[UserCompletedTaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UpdateUserProfileRequest(BaseModel):

    username: str | None = None
    email: EmailStr | None = None
    fio: str | None = None
    avatar_url: str | None = None
    telegram: str | None = None
    phone_number: str | None = None


class UpdateUserProfileResponse(BaseModel):

    username: str
    email: EmailStr
    fio: str
    avatar_url: str | None = None
    telegram: str | None = None
    phone_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CreatePreSignedURLResponse(BaseModel):

    upload_url: str

    model_config = ConfigDict(from_attributes=True)
