from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from app.users.schema import UserShortResponse


class NotificationResponse(BaseModel):

    uuid: UUID
    content: str
    recipient_user_uuid: UUID | None = None
    recipient_user: UserShortResponse | None = None
    sender_user_uuid: UUID | None = None
    sender_user: UserShortResponse | None = None
    created_at: datetime
