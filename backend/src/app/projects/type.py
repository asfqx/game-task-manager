from typing import TypedDict
from uuid import UUID

class ProjectFilterPayload(TypedDict, total=False):

    creator_uuid: UUID
    title: str
    limit: int
    cursor: UUID
