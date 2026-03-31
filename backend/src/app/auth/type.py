from datetime import datetime
from typing import TypedDict

class AuthJWTPayload(TypedDict):

    sub: str
    role: str
    exp: datetime
    iat: datetime
    jti: str
