from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enum import InvitationStatus
from app.users.schema import UserShortResponse


class CreateInvitationRequest(BaseModel):

    team_uuid: UUID
    recipient_login: str = Field(min_length=3, max_length=255)


class InvitationProjectResponse(BaseModel):

    uuid: UUID
    title: str

    model_config = ConfigDict(from_attributes=True)


class InvitationTeamResponse(BaseModel):

    uuid: UUID
    name: str
    project_uuid: UUID
    project_title: str

    model_config = ConfigDict(from_attributes=True)


class InvitationResponse(BaseModel):

    uuid: UUID
    project_uuid: UUID
    project: InvitationProjectResponse
    team_uuid: UUID
    team: InvitationTeamResponse
    sender_user_uuid: UUID | None = None
    sender_user: UserShortResponse | None = None
    recipient_user_uuid: UUID
    recipient_user: UserShortResponse | None = None
    recipient_login: str
    status: InvitationStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
