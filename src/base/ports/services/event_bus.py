from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EventBusMessage:
    event_type: str
    payload: dict[str, Any]
    headers: Mapping[str, str] | None = None
    message_id: str | None = None


EventBusHandler = Callable[[EventBusMessage], Awaitable[None]]


class EventBusPort(ABC):
    @abstractmethod
    def is_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, message: EventBusMessage) -> None:
        raise NotImplementedError

    @abstractmethod
    async def consume(self, *, handler: EventBusHandler) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
