from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from app.auth.constant import (
    MAX_LOGIN_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_LOGIN_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
    MAX_FIO_LENGTH,
    MIN_FIO_LENGTH,
)
from app.enum import UserRole


class CreateRegisterRequest(BaseModel):

    email: EmailStr

    username: str = Field(
        ...,
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
    )

    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
    )

    fio: str = Field(
        ...,
        min_length=MIN_FIO_LENGTH,
        max_length=MAX_FIO_LENGTH,
    )
    
    role: UserRole


class CreateSuperuserRequest(CreateRegisterRequest):
    
    role: UserRole = UserRole.ADMIN


class CreateLoginRequest(BaseModel):

    login: str = Field(
        ...,
        min_length=MIN_LOGIN_LENGTH,
        max_length=MAX_LOGIN_LENGTH,
    )

    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
    )


class TokenPairResponse(BaseModel):

    access_token: str
    refresh_token: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class GetLogoutResponse(BaseModel):

    message: str

    model_config = ConfigDict(
        from_attributes=True,
    )
