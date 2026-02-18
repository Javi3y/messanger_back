from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence


class AbstractCacheRepository(ABC):
    @abstractmethod
    async def get(self, *, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def set(self, *, key: str, value: Any, ttl: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, *, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def incr(self, *, key: str, amount: int = 1, ttl: int | None = None) -> int:
        raise NotImplementedError

    @abstractmethod
    async def decr(self, *, key: str, amount: int = 1, ttl: int | None = None) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_many(self, *, keys: Sequence[str]) -> Mapping[str, Any | None]:
        raise NotImplementedError

    @abstractmethod
    async def set_many(
        self, *, mapping: Mapping[str, Any], ttl: int | None = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self, *, prefix: str | None = None) -> None:
        raise NotImplementedError
