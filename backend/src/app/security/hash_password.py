from passlib.context import CryptContext

from .constant import (
    ARGON2_MEMORY_COST,
    ARGON2_TIME_COST,
    ARGON2_PARALLELISM,
    PASSWORD_HASH_SCHEMES,
    PASSWORD_HASH_DEPRECATED,
)


class Argon2Hasher:

    __ctx = CryptContext(
        schemes=PASSWORD_HASH_SCHEMES,
        deprecated=PASSWORD_HASH_DEPRECATED,
        argon2__memory_cost=ARGON2_MEMORY_COST,
        argon2__time_cost=ARGON2_TIME_COST,
        argon2__parallelism=ARGON2_PARALLELISM,
    )

    @classmethod
    def hash(cls, password: str) -> str:

        return cls.__ctx.hash(password)

    @classmethod
    def verify(cls, plain_password: str, hashed_password: str) -> bool:

        return cls.__ctx.verify(plain_password, hashed_password)
