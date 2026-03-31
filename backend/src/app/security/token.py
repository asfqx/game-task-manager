from typing import Any

from jose import jwt

from app.core import settings

from .constant import DEFAULT_PASSWORD_HASH_ALGORITHM


class JWTUtils:

    @staticmethod
    def encode(
        payload: dict[str, Any],
        *,
        secret: str = settings.hash_secret_key,
        algorithm: str = DEFAULT_PASSWORD_HASH_ALGORITHM,
    ) -> str:

        return jwt.encode(payload, secret, algorithm=algorithm)

    @staticmethod
    def decode(
        token: str,
        *,
        secret: str = settings.hash_secret_key,
        algorithm: str = DEFAULT_PASSWORD_HASH_ALGORITHM,
    ) -> dict[str, Any]:

        return jwt.decode(token, secret, algorithms=[algorithm])
