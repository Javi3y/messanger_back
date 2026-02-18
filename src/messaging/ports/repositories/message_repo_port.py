from abc import ABC, abstractmethod
from datetime import datetime

from src.base.ports.repositories.repository import AbstractRepository
from src.messaging.domain.entities.message import Message


class MessageRepositoryPort(AbstractRepository, ABC):

    @abstractmethod
    async def add(
        self,
        *,
        entity: Message,
        **kwargs,
    ) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        *,
        entity: Message,
        **kwargs,
    ) -> Message:
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
    ) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> Message | None:
        raise NotImplementedError

    @abstractmethod
    async def get_pending_to_send_before(
        self,
        *,
        before: datetime,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
        lock: bool = False,
        skip_locked: bool = True,
        **kwargs,
    ) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def get_pending_for_request_to_send_before(
        self,
        *,
        request_id: int,
        before: datetime,
        limit: int = 100,
        lock: bool = False,
        skip_locked: bool = True,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def get_next_pending_sending_time_for_request(
        self,
        *,
        request_id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> datetime | None:
        raise NotImplementedError
