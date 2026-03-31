from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints


class PasswordResetConfirmRequest(BaseModel):
    
    email: EmailStr
    new_password: Annotated[str, StringConstraints(min_length=6)]
