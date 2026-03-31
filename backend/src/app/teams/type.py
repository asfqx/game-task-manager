from typing import TypedDict
from uuid import UUID

class TeamFilterPayload(TypedDict, total=False):

    project_uuid: UUID
    lead_uuid: UUID
    name: str
    limit: int
    cursor: UUID
