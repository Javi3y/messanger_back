import inspect
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from src.base.application.outbox.registry import OutboxRegistry
from src.base.domain.events.outbox_domain_event import OutboxDomainEvent
from src.files.ports.services.file_service import FileServicePort
from src.importing.application.registry.import_registry import ImportRegistry
from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)
from src.importing.ports.services.tabular_reader_port import TabularReaderPort
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.base.ports.services.event_bus import EventBusMessage, EventBusPort

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 10


def _backoff(attempts: int) -> timedelta:
    seconds = min(60, 2 ** max(0, attempts - 1))
    return timedelta(seconds=seconds)


def _build_handler_kwargs(
    handler: Callable,
    *,
    uow: AsyncUnitOfWork,
    event: OutboxDomainEvent | None,
    messenger_registry: MessengerRegistry,
    file_service: FileServicePort,
    tabular_reader: TabularReaderPort,
    import_staging_repo: ImportStagingRepositoryPort,
    import_registry: ImportRegistry,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"uow": uow, "event": event}

    sig = inspect.signature(handler)
    for name in sig.parameters:
        if name in ("uow", "event"):
            continue

        if name == "messenger_registry":
            kwargs[name] = messenger_registry
        elif name == "file_service":
            kwargs[name] = file_service
        elif name == "tabular_reader":
            kwargs[name] = tabular_reader
        elif name == "import_staging_repo":
            kwargs[name] = import_staging_repo
        elif name == "import_registry":
            kwargs[name] = import_registry

    return kwargs


async def dispatch_outbox_events(
    *,
    uow_factory: Callable[[], AsyncUnitOfWork],
    outbox_registry: OutboxRegistry,
    messenger_registry: MessengerRegistry,
    file_service: FileServicePort,
    tabular_reader: TabularReaderPort,
    import_staging_repo: ImportStagingRepositoryPort,
    import_registry: ImportRegistry,
    dispatch_strategy: str,
    event_bus: EventBusPort,
    batch_size: int = 50,
) -> dict[str, int]:
    now = datetime.now(timezone.utc)

    processed = 0
    rescheduled = 0
    dead_lettered = 0

    strategy = dispatch_strategy
    if strategy not in ("direct", "broker"):
        raise RuntimeError(
            f"Invalid outbox_dispatch_strategy={strategy!r} (use 'direct' or 'broker')"
        )

    if strategy == "broker" and not event_bus.is_enabled():
        raise RuntimeError(
            "outbox_dispatch_strategy='broker' but broker is disabled "
            "(set broker_driver='rabbitmq' and broker_url)"
        )

    async with uow_factory() as uow:
        events = await uow.outbox_event_repo.get_ready(
            now=now,
            limit=batch_size,
            lock=True,
            skip_locked=True,
        )

        for ev in events:
            ev.attempts = (ev.attempts or 0) + 1

            try:
                if strategy == "direct":
                    handler = outbox_registry.get_handler(ev.event_type)
                    if handler is None:
                        ev.last_error = (
                            f"No handler registered for event_type={ev.event_type}"
                        )
                        ev.processed_at = now
                        await uow.outbox_event_repo.update(entity=ev)
                        dead_lettered += 1
                        continue

                    typed_event = outbox_registry.build_event(ev.event_type, ev.payload)
                    if typed_event is None:
                        ev.last_error = (
                            f"No event class registered for event_type={ev.event_type}"
                        )
                        ev.processed_at = now
                        await uow.outbox_event_repo.update(entity=ev)
                        dead_lettered += 1
                        continue

                    kwargs = _build_handler_kwargs(
                        handler,
                        uow=uow,
                        event=typed_event,
                        messenger_registry=messenger_registry,
                        file_service=file_service,
                        tabular_reader=tabular_reader,
                        import_staging_repo=import_staging_repo,
                        import_registry=import_registry,
                    )
                    await handler(**kwargs)

                else:
                    # strategy == "broker": publish only; consumers execute handlers
                    headers = {
                        "outbox_id": str(ev.id),
                        "attempts": str(ev.attempts or 0),
                    }
                    if ev.dedup_key:
                        headers["dedup_key"] = ev.dedup_key
                    if ev.aggregate_type:
                        headers["aggregate_type"] = ev.aggregate_type
                    if ev.aggregate_id:
                        headers["aggregate_id"] = ev.aggregate_id

                    await event_bus.publish(
                        EventBusMessage(
                            event_type=ev.event_type,
                            payload=ev.payload,
                            headers=headers,
                            message_id=str(ev.id),
                        )
                    )

                ev.last_error = None
                ev.processed_at = now
                await uow.outbox_event_repo.update(entity=ev)
                processed += 1

            except Exception as e:
                logger.exception(
                    "Outbox dispatch failed event_id=%s type=%s strategy=%s",
                    ev.id,
                    ev.event_type,
                    strategy,
                )
                ev.last_error = str(e)[:1000]

                if ev.attempts >= MAX_ATTEMPTS:
                    ev.processed_at = now
                    await uow.outbox_event_repo.update(entity=ev)
                    dead_lettered += 1
                else:
                    ev.available_at = now + _backoff(ev.attempts)
                    await uow.outbox_event_repo.update(entity=ev)
                    rescheduled += 1

        await uow.commit()

    return {
        "processed": processed,
        "rescheduled": rescheduled,
        "dead_lettered": dead_lettered,
    }
