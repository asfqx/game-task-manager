from app.core.env import settings

from .adapters import BaseCacheAdapter, MemoryCacheAdapter, RedisAdapter


_cache_adapters: dict[str, BaseCacheAdapter] = {}


def get_cache_adapter(
    provider_type: str = settings.cache_adapter,
) -> BaseCacheAdapter:

    normalized_provider = provider_type.lower()

    if normalized_provider in _cache_adapters:
        return _cache_adapters[normalized_provider]

    match normalized_provider:
        case "redis" | "keydb":
            adapter: BaseCacheAdapter = RedisAdapter(settings.cache_url)
        case _:
            adapter = MemoryCacheAdapter()

    _cache_adapters[normalized_provider] = adapter
    return adapter


CacheAdapter = get_cache_adapter()
