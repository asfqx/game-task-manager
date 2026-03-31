from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.enum import Gender
from app.lvls.schema import LvlSummaryResponse


class UserShortResponse(BaseModel):

    uuid: UUID
    username: str
    fio: str


class UserTeamSummaryResponse(BaseModel):

    team_uuid: UUID
    team_name: str
    project_uuid: UUID
    project_title: str
    is_team_lead: bool
    xp_amount: int
    lvl_uuid: UUID | None = None
    lvl: LvlSummaryResponse | None = None


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


class CreatePreSignedURLResponse(BaseModel):

    upload_url: str
