import asyncio
from logging.config import fileConfig

from pydantic import ValidationError
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from alembic import context
from app.core import Base, settings
from app.projects.model import Project
from app.users.model import User
from app.notifications.model import Notification
from app.teams.model import Team, TeamMember
from app.lvls.model import Lvl
from app.tasks.model import Task
from app.system_logging.model import UserActionLog, XpAccrualLog

config = context.config

try:
    config.set_main_option("sqlalchemy.url", settings.db_url)
except ValidationError as e:
    msg = f"Некорректные настройки: {e}"
    raise RuntimeError(msg) from e

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in online mode with async engine."""
    connectable: AsyncEngine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
