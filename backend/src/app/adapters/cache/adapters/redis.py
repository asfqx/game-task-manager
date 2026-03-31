import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from app.adapters.cache.exception import GetRuntimeError

from .base import BaseCacheAdapter


RedisValue = bytes | str | memoryview


class RedisAdapter(BaseCacheAdapter):

    def __init__(
        self,
        redis_url: str,
    ) -> None:

        self.redis_url = redis_url
        self._client: Redis = redis.from_url(self.redis_url)  # pyright: ignore[reportUnknownMemberType]

    @property
    def client(self) -> Redis:

        return self._client

    async def get(
        self,
        key: str,
    ) -> RedisValue | None:

        if not self._client:
            msg = "Ошибка выполнения операции с CacheAdapter"
            raise GetRuntimeError(msg)

        value = await self._client.get(key)

        if value is None:
            return None
        try:
            text = value.decode("utf-8")
            return json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return value.decode("utf-8")

    async def set(
        self,
        key: str,
        value: RedisValue,
        expire: int | None = None,
    ) -> None:

        if not self._client:
            msg = "Ошибка выполнения операции с CacheAdapter"
            raise GetRuntimeError(msg)

        if isinstance(value, str):
            data = value.encode("utf-8")
        elif isinstance(value, memoryview):
            data = value.tobytes()
        else:
            data = value

        await self._client.set(key, data, ex=expire)

    async def publish(
        self,
        channel: str,
        value: Any,
    ) -> int:

        if not self._client:
            msg = "РћС€РёР±РєР° РІС‹РїРѕР»РЅРµРЅРёСЏ РѕРїРµСЂР°С†РёРё СЃ CacheAdapter"
            raise GetRuntimeError(msg)

        if isinstance(value, bytes):
            data = value
        elif isinstance(value, memoryview):
            data = value.tobytes()
        elif isinstance(value, str):
            data = value.encode("utf-8")
        else:
            data = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")

        return int(await self._client.publish(channel, data))


    async def delete(self, key: str) -> None:

        if not self._client:
            msg = "Ошибка выполнения операции с CacheAdapter"
            raise GetRuntimeError(msg)

        await self._client.delete(key)

    async def exists(self, key: str) -> bool:

        if not self._client:
            msg = "Ошибка выполнения операции с CacheAdapter"
            raise GetRuntimeError(msg)

        return bool(await self.client.exists(key))
