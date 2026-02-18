import inspect
import logging
from typing import Any, Callable

from src.base.application.outbox.registry import OutboxRegistry
from src.base.domain.events.outbox_domain_event import OutboxDomainEvent
from src.base.ports.services.event_bus import EventBusMessage, EventBusPort
from src.base.ports.unit_of_work import AsyncUnitOfWork

logger = logging.getLogger(__name__)


def _build_handler_kwargs(
    handler: Callable,
    *,
    uow: AsyncUnitOfWork,
    event: OutboxDomainEvent | None,
    container: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"uow": uow, "event": event}

    sig = inspect.signature(handler)
    for name in sig.parameters:
        if name in ("uow", "event"):
            continue

        if name == "messenger_registry":
            kwargs[name] = container.messenger_registry()
        elif name == "file_service":
            kwargs[name] = container.file_service()
        elif name == "tabular_reader":
            kwargs[name] = container.tabular_reader()
        elif name == "import_staging_repo":
            kwargs[name] = container.import_staging_repo()
        elif name == "import_registry":
            kwargs[name] = container.import_registry()

    return kwargs


async def consume_event_bus_messages(
    *,
    uow_factory: Callable[[], AsyncUnitOfWork],
    outbox_registry: OutboxRegistry,
    container: Any,
    event_bus: EventBusPort,
    batch_size: int = 1,  # unused; kept for worker runner compatibility
) -> dict[str, int]:
    if not event_bus.is_enabled():
        raise RuntimeError(
            "consume_event_bus_messages requires broker_driver != 'none'"
        )

    processed = 0

    async def _handle(msg: EventBusMessage) -> None:
        nonlocal processed

        handler = outbox_registry.get_handler(msg.event_type)
        if handler is None:
            # Not for this service — ack by returning
            logger.info("No handler for event_type=%s (dropping)", msg.event_type)
            return

        typed_event = outbox_registry.build_event(msg.event_type, msg.payload)

        async with uow_factory() as uow:
            kwargs = _build_handler_kwargs(
                handler,
                uow=uow,
                event=typed_event,
                container=container,
            )
            await handler(**kwargs)
            await uow.commit()

        processed += 1

    try:
        await event_bus.consume(handler=_handle)
    finally:
        await event_bus.close()

    return {"processed": processed}
