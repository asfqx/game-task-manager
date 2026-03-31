from enum import StrEnum


class UserRole(StrEnum):
    
    ADMIN = "admin"
    USER = "user"


class UserStatus(StrEnum):

    ACTIVE = "ACTIVE"
    BANNED = "BANNED"


class Gender(StrEnum):
    
    MALE = "MALE"
    FEMALE = "FEMALE"


class TaskStatus(StrEnum):
    
    CREATED = "CREATED"
    IN_WORK = "IN_WORK"
    ON_CHECK = "ON_CHECK"
    DONE = "DONE"
    