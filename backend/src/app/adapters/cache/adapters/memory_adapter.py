from typing import Any

from .base import BaseCacheAdapter


class MemoryCacheAdapter(BaseCacheAdapter):

    def __init__(self) -> None:

        self._store: dict[str, Any] = {}

    async def get(
        self,
        key: str,
    ) -> Any | None:  # noqa: ANN401

        return self._store.get(key)

    async def set(
        self,
        key: str,
        value: Any,  # noqa: ANN401
        expire: int | None = None,  # noqa: ARG002
    ) -> None:

        self._store[key] = value

    async def delete(
        self,
        key: str,
    ) -> None:

        self._store.pop(key, None)

    async def exists(
        self,
        key: str,
    ) -> bool:

        return key in self._store
