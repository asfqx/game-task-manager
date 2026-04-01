import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any

from .base import BaseCacheAdapter


class MemoryCacheAdapter(BaseCacheAdapter):

    def __init__(self) -> None:

        self._store: dict[str, Any] = {}
        self._channels: dict[str, list[asyncio.Queue[str]]] = defaultdict(list)

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

    async def publish(
        self,
        channel: str,
        value: Any,
    ) -> int:

        if isinstance(value, str):
            payload = value
        else:
            payload = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        subscribers = list(self._channels.get(channel, []))

        for subscriber in subscribers:
            await subscriber.put(payload)

        return len(subscribers)

    def subscribe(
        self,
        channel: str,
        *,
        timeout: float = 15.0,
    ) -> AsyncIterator[str | None]:

        async def iterator() -> AsyncIterator[str | None]:
            queue: asyncio.Queue[str] = asyncio.Queue()
            self._channels[channel].append(queue)

            try:
                while True:
                    try:
                        yield await asyncio.wait_for(
                            queue.get(),
                            timeout=timeout,
                        )
                    except TimeoutError:
                        yield None
            finally:
                subscribers = self._channels.get(channel)

                if subscribers and queue in subscribers:
                    subscribers.remove(queue)

                if subscribers == []:
                    self._channels.pop(channel, None)

        return iterator()
