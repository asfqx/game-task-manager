from app.core.env import settings

from .adapters import BaseCacheAdapter, MemoryCacheAdapter, RedisAdapter


def get_cache_adapter(
    provider_type: str = settings.cache_adapter,
) -> BaseCacheAdapter:

    match provider_type:
        case "redis":
            return RedisAdapter(settings.cache_url)
        case _:
            return MemoryCacheAdapter()


CacheAdapter = get_cache_adapter()
