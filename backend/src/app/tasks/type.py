from typing import TypedDict
from uuid import UUID

from app.enum import TaskStatus

class TaskFilterPayload(TypedDict, total=False):

    team_uuid: UUID
    issuer_user_uuid: UUID
    assignee_user_uuid: UUID
    status: TaskStatus
    limit: int
    cursor: UUID
