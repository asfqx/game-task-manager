from pydantic import BaseModel, ConfigDict


class CreateTokenPairResponse(BaseModel):

    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class GetAccessTokenRequest(BaseModel):

    access_token: str

    model_config = ConfigDict(from_attributes=True)


class GetUserRoleResponse(BaseModel):

    role: str

    model_config = ConfigDict(from_attributes=True)
