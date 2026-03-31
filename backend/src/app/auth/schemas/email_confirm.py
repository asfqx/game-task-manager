from pydantic import BaseModel, EmailStr


class EmailConfirmRequest(BaseModel):
    
    email: EmailStr
