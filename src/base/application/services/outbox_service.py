from datetime import datetime, timezone

from src.base.domain.entities.outbox_event import OutboxEvent
from src.base.domain.events.outbox_domain_event import OutboxDomainEvent
from src.base.ports.unit_of_work import AsyncUnitOfWork


class OutboxService:
    def __init__(self, uow: AsyncUnitOfWork) -> None:
        self.uow = uow

    async def publish(self, event: OutboxDomainEvent) -> OutboxEvent:
        now = datetime.now(timezone.utc)

        row = OutboxEvent(
            event_type=event.event_type(),
            payload=event.payload(),
            available_at=event.available_at or now,
            dedup_key=event.dedup_key,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
        )
        return await self.uow.outbox_event_repo.add(entity=row)
