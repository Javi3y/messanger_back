from abc import ABC, abstractmethod

from src.base.ports.repositories.repository import AbstractRepository
from src.users.domain.entities.user import User


class UserRepositoryPort(AbstractRepository, ABC):

    @abstractmethod
    async def add(
        self,
        *,
        entity: User,
        **kwargs,
    ) -> User:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        *,
        entity: User,
        **kwargs,
    ) -> User:
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
    async def get(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(
        self,
        *,
        username: str,
        include_deleted: bool = False,
        **kwargs,
    ) -> User | None:
        raise NotImplementedError
