from abc import ABC, abstractmethod
from typing import Any


class AbstractRepository(ABC):
    def __init__(self, session: Any) -> None:
        self.session = session

    @abstractmethod
    async def add(
        self,
        *,
        entity: Any,
        **kwargs,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        *,
        id: int,
        soft_delete: bool = True,
        **kwargs,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        *,
        entity: Any,
        **kwargs,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def get(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> Any | None:
        raise NotImplementedError
