from src.base.ports.services.event_bus import (
    EventBusHandler,
    EventBusMessage,
    EventBusPort,
)


class NoopEventBus(EventBusPort):

    def is_enabled(self) -> bool:
        return False

    async def publish(self, message: EventBusMessage) -> None:
        return None

    async def consume(self, *, handler: EventBusHandler) -> None:
        raise RuntimeError("Event bus is disabled (broker_driver=none).")

    async def close(self) -> None:
        return None
