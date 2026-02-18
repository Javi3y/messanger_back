import json
from datetime import datetime, UTC
from typing import Any

from redis.asyncio import Redis

from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)


class RedisImportStagingRepository(ImportStagingRepositoryPort):
    KEY_PREFIX = "importing"

    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client

    def _meta_key(self, job_key: str) -> str:
        return f"{self.KEY_PREFIX}:job:{job_key}:meta"

    def _rows_key(self, job_key: str) -> str:
        return f"{self.KEY_PREFIX}:job:{job_key}:rows"

    async def create_job(
        self, *, job_key: str, meta: dict[str, Any], ttl_seconds: int
    ) -> None:
        now = datetime.now(UTC).isoformat()
        meta = {**meta, "created_at": now, "updated_at": now}
        pipe = self.redis.pipeline()
        pipe.setex(self._meta_key(job_key), ttl_seconds, json.dumps(meta))
        pipe.delete(self._rows_key(job_key))
        await pipe.execute()

    async def update_meta(
        self, *, job_key: str, updates: dict[str, Any], ttl_seconds: int
    ) -> None:
        key = self._meta_key(job_key)
        raw = await self.redis.get(key)
        meta = json.loads(raw) if raw else {}
        meta.update(updates)
        meta["updated_at"] = datetime.now(UTC).isoformat()
        await self.redis.setex(key, ttl_seconds, json.dumps(meta))

    async def get_meta(self, *, job_key: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._meta_key(job_key))
        return json.loads(raw) if raw else None

    async def push_rows(
        self, *, job_key: str, rows: list[dict[str, Any]], ttl_seconds: int
    ) -> int:
        if not rows:
            return 0
        key = self._rows_key(job_key)
        pipe = self.redis.pipeline()
        for r in rows:
            pipe.rpush(key, json.dumps(r, default=str))
        pipe.expire(key, ttl_seconds)
        await pipe.execute()
        return len(rows)

    async def pop_rows(self, *, job_key: str, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        key = self._rows_key(job_key)
        pipe = self.redis.pipeline()
        for _ in range(limit):
            pipe.lpop(key)
        data = await pipe.execute()
        out: list[dict[str, Any]] = []
        for item in data:
            if item is None:
                continue
            out.append(json.loads(item))
        return out

    async def remaining(self, *, job_key: str) -> int:
        return int(await self.redis.llen(self._rows_key(job_key)))

    async def add_errors(
        self,
        *,
        job_key: str,
        errors: list[dict[str, Any]],
        ttl_seconds: int,
        max_errors: int,
    ) -> None:
        if not errors:
            return
        meta = await self.get_meta(job_key=job_key) or {}
        current = meta.get("errors", [])
        if not isinstance(current, list):
            current = []
        if len(current) >= max_errors:
            return
        remaining = max_errors - len(current)
        current.extend(errors[:remaining])
        await self.update_meta(
            job_key=job_key, updates={"errors": current}, ttl_seconds=ttl_seconds
        )

    async def cleanup(self, *, job_key: str) -> None:
        await self.redis.delete(self._meta_key(job_key), self._rows_key(job_key))
