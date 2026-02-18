from abc import ABC, abstractmethod
from typing import Any


class ImportStagingRepositoryPort(ABC):
    @abstractmethod
    async def create_job(
        self,
        *,
        job_key: str,
        meta: dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_meta(
        self, *, job_key: str, updates: dict[str, Any], ttl_seconds: int
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_meta(self, *, job_key: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def push_rows(
        self, *, job_key: str, rows: list[dict[str, Any]], ttl_seconds: int
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def pop_rows(self, *, job_key: str, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def remaining(self, *, job_key: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def add_errors(
        self,
        *,
        job_key: str,
        errors: list[dict[str, Any]],
        ttl_seconds: int,
        max_errors: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self, *, job_key: str) -> None:
        raise NotImplementedError
