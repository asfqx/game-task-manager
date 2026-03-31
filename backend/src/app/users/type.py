from typing import TypedDict

from app.enum import Gender, UserRole, UserStatus

class UserFilterPayload(TypedDict, total=False):

    username: str
    email: str
    fio: str
    gender: Gender
    role: UserRole
    status: UserStatus
    limit: int
