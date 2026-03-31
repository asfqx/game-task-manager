import asyncpg  # pyright: ignore[reportMissingTypeStubs]
import sqlalchemy.exc as sqlalchemy_exc


DB_CONNECTION_ERRORS: tuple[type[BaseException], ...] = (
    asyncpg.CannotConnectNowError,
    asyncpg.ConnectionDoesNotExistError,
    asyncpg.InterfaceError,
    asyncpg.PostgresConnectionError,
    asyncpg.PostgresError,
    sqlalchemy_exc.SQLAlchemyError,
)
DB_CONNECTION_ERROR_MESSAGE = "Ошибка подключения к базе данных"


DB_MODEL_ERRORS: tuple[type[BaseException], ...] = (
    asyncpg.exceptions.UndefinedTableError,
    sqlalchemy_exc.ProgrammingError,
)
DB_MODEL_ERROR_MESSAGE = "Ошибка схемы базы данных"
