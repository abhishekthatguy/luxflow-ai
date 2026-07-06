from abc import ABC, abstractmethod

import redis


class CacheClient(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None: ...

    @abstractmethod
    def set(self, key: str, value: str, ttl: int = 60) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class RedisCacheClient(CacheClient):
    def __init__(self, url: str) -> None:
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ttl: int = 60) -> None:
        self._client.setex(key, ttl, value)

    def delete(self, key: str) -> None:
        self._client.delete(key)


def get_cache_client(url: str) -> CacheClient:
    return RedisCacheClient(url)
