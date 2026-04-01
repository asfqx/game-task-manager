from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.system_logging.type import UserActionLogDetailsPayload
from app.users.schema import UserShortResponse


class XpAccrualLogTaskResponse(BaseModel):

    uuid: UUID
    title: str
    team_uuid: UUID
    team_name: str
    project_uuid: UUID
    project_title: str

    model_config = ConfigDict(from_attributes=True)


class XpAccrualLogResponse(BaseModel):

    uuid: UUID
    issued_at: datetime
    xp_amount: int
    recipient_user_uuid: UUID | None = None
    recipient_user: UserShortResponse | None = None
    issuer_user_uuid: UUID | None = None
    issuer_user: UserShortResponse | None = None
    task_uuid: UUID | None = None
    task: XpAccrualLogTaskResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class UserActionLogResponse(BaseModel):

    uuid: UUID
    issued_at: datetime
    actor_user_uuid: UUID | None = None
    actor_user: UserShortResponse | None = None
    action: str
    entity_type: str | None = None
    entity_uuid: UUID | None = None
    details: UserActionLogDetailsPayload | None = None

    model_config = ConfigDict(from_attributes=True)
