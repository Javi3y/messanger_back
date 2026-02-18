from abc import ABC, abstractmethod
from datetime import datetime

from src.base.domain.entities.outbox_event import OutboxEvent
from src.base.ports.repositories.repository import AbstractRepository


class OutboxEventRepositoryPort(AbstractRepository, ABC):
    @abstractmethod
    async def add(self, *, entity: OutboxEvent, **kwargs) -> OutboxEvent:
        raise NotImplementedError

    @abstractmethod
    async def update(self, *, entity: OutboxEvent, **kwargs) -> OutboxEvent:
        raise NotImplementedError

    @abstractmethod
    async def get_ready(
        self,
        *,
        now: datetime,
        limit: int = 100,
        lock: bool = False,
        skip_locked: bool = True,
        **kwargs,
    ) -> list[OutboxEvent]:
        raise NotImplementedError
