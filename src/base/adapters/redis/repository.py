import json
from datetime import datetime
from typing import Any, Mapping, Sequence, Dict

from redis.asyncio import Redis

from src.base.ports.repositories.cache_repository import AbstractCacheRepository


def _serialize(value: Any) -> bytes:

    def default(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(value, default=default).encode("utf-8")


def _deserialize(raw: bytes | None) -> Any | None:
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return raw


class RedisCacheRepository(AbstractCacheRepository):
    def __init__(self, redis_client: "Redis", *, key_prefix: str | None = None):
        if Redis is None:
            raise RuntimeError(
                "redis.asyncio.Redis is required. Install 'redis' package."
            )
        self._redis: "Redis" = redis_client
        self._prefix = (key_prefix or "").strip()
        if self._prefix and not self._prefix.endswith(":"):
            self._prefix += ":"

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}" if self._prefix else key

    async def get(self, *, key: str) -> Any | None:
        raw = await self._redis.get(self._k(key))
        return _deserialize(raw)

    async def set(self, *, key: str, value: Any, ttl: int | None = None) -> None:
        raw = _serialize(value)
        if ttl is None:
            await self._redis.set(self._k(key), raw)
        else:
            await self._redis.set(self._k(key), raw, ex=int(ttl))

    async def delete(self, *, key: str) -> None:
        await self._redis.delete(self._k(key))

    async def exists(self, *, key: str) -> bool:
        return bool(await self._redis.exists(self._k(key)))

    async def incr(self, *, key: str, amount: int = 1, ttl: int | None = None) -> int:
        new = await self._redis.incrby(self._k(key), int(amount))
        if ttl is not None:
            await self._redis.expire(self._k(key), int(ttl))
        return int(new)

    async def decr(self, *, key: str, amount: int = 1, ttl: int | None = None) -> int:
        new = await self._redis.decrby(self._k(key), int(amount))
        if ttl is not None:
            await self._redis.expire(self._k(key), int(ttl))
        return int(new)

    async def get_many(self, *, keys: Sequence[str]) -> Mapping[str, Any | None]:
        if not keys:
            return {}
        real_keys = [self._k(k) for k in keys]
        raws = await self._redis.mget(*real_keys)
        result: Dict[str, Any | None] = {}
        for k, raw in zip(keys, raws):
            result[k] = _deserialize(raw)
        return result

    async def set_many(
        self, *, mapping: Mapping[str, Any], ttl: int | None = None
    ) -> None:
        if not mapping:
            return
        kv = {self._k(k): _serialize(v) for k, v in mapping.items()}
        await self._redis.mset(kv)
        if ttl is not None:
            async def _expire_all():
                for k in kv.keys():
                    await self._redis.expire(k, int(ttl))

            for k in kv.keys():
                await self._redis.expire(k, int(ttl))

    async def clear(self, *, prefix: str | None = None) -> None:
        p = prefix if prefix is not None else self._prefix or ""
        if p == "":
            raise RuntimeError(
                "Clearing entire Redis DB is dangerous. Pass a non-empty prefix."
            )
        if not p.endswith(":"):
            p = p + ":"
        pattern = f"{p}*"
        cur = "0"
        async for key in self._redis.scan_iter(match=pattern):
            await self._redis.delete(key)
