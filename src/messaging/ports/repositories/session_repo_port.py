from abc import ABC, abstractmethod
from uuid import UUID

from src.base.ports.repositories.repository import AbstractRepository
from src.messaging.domain.entities.session import Session, MessengerType


class SessionRepositoryPort(AbstractRepository, ABC):

    @abstractmethod
    async def add(self, *, entity: Session, **kwargs) -> Session:
        raise NotImplementedError

    @abstractmethod
    async def update(self, *, entity: Session, **kwargs) -> Session:
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
    ) -> list[Session]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> Session | None:
        raise NotImplementedError

    # domain-specific helpers

    @abstractmethod
    async def get_by_uuid(
        self,
        *,
        uuid: UUID,
        include_deleted: bool = False,
        **kwargs,
    ) -> Session | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_phone_and_type(
        self,
        *,
        phone_number: str,
        session_type: MessengerType,
        include_deleted: bool = False,
        **kwargs,
    ) -> Session | None:
        raise NotImplementedError
