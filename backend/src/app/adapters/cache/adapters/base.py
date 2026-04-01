from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class BaseCacheAdapter(ABC):

    @abstractmethod
    async def get(
        self,
        key: str,
    ) -> Any | None:
        ...

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> None:
        ...

    @abstractmethod
    async def delete(
        self,
        key: str,
    ) -> None:
        ...

    @abstractmethod
    async def exists(
        self,
        key: str,
    ) -> bool:
        ...

    @abstractmethod
    async def publish(
        self,
        channel: str,
        value: Any,
    ) -> int:
        ...

    @abstractmethod
    def subscribe(
        self,
        channel: str,
        *,
        timeout: float = 15.0,
    ) -> AsyncIterator[str | None]:
        ...
