from abc import ABC, abstractmethod

from src.base.ports.repositories.repository import AbstractRepository
from src.messaging.domain.entities.messaging_request import MessagingRequest


class MessagingRequestRepositoryPort(AbstractRepository, ABC):
    @abstractmethod
    async def add(
        self,
        *,
        entity: MessagingRequest,
        **kwargs,
    ) -> MessagingRequest:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        *,
        entity: MessagingRequest,
        **kwargs,
    ) -> MessagingRequest:
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
    ) -> list[MessagingRequest]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> MessagingRequest | None:
        raise NotImplementedError
