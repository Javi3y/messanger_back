from abc import ABC, abstractmethod
from typing import Sequence

from src.base.ports.repositories.repository import AbstractRepository
from src.users.domain.enums.user_type import UserType
from src.users.domain.entities.base_user import BaseUser


class BaseUserRepositoryPort(AbstractRepository, ABC):
    @abstractmethod
    async def add(
        self,
        *,
        entity: BaseUser,
        **kwargs,
    ) -> BaseUser:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        *,
        entity: BaseUser,
        **kwargs,
    ) -> BaseUser:
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
    ) -> list[BaseUser]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> BaseUser | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(
        self,
        *,
        username: str,
        include_deleted: bool = False,
        **kwargs,
    ) -> BaseUser | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_type(
        self,
        *,
        user_type: UserType,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> Sequence[BaseUser]:
        raise NotImplementedError
