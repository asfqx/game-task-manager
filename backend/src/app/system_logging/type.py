from typing import TypedDict
from uuid import UUID

from app.enum import UserRole


class UserActionLogDetailsPayload(TypedDict, total=False):

    role: UserRole | str
    title: str
    project_uuid: str
    name: str
    added_by_user_uuid: str
    member_user_uuid: str
    removed_by_user_uuid: str
    changed_fields: list[str]
    team_uuid: str
    assignee_user_uuid: str
    review_comment: str
    target_user_uuid: str


class XpAccrualLogFilterPayload(TypedDict, total=False):

    recipient_user_uuid: UUID
    issuer_user_uuid: UUID
    task_uuid: UUID
    team_uuid: UUID
    limit: int
    cursor: UUID


class UserActionLogFilterPayload(TypedDict, total=False):

    actor_user_uuid: UUID
    action: str
    entity_type: str
    entity_uuid: UUID
    limit: int
    cursor: UUID
