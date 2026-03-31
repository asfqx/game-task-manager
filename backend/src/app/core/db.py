from typing import Annotated, AsyncGenerator
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .env import settings


class Base(DeclarativeBase, AsyncAttrs):
    
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        
        return cls.__name__.lower() + "s"
    
    
engine = create_async_engine(
    settings.db_url   
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession]:
    
    async with AsyncSessionLocal() as async_session:
        yield async_session
        
DBSession = Annotated[AsyncSession, Depends(get_async_session)]
