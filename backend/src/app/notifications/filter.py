from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, Field


class NotificationFilterQueryParams(BaseModel):

    sender_user_uuid: UUID | None = None
    limit: int | None = Field(default=50, ge=1, le=1000)


NotificationFilterDepends = Annotated[NotificationFilterQueryParams, Depends()]
