"""Messenger registry for plugin-based messenger discovery."""

from src.messaging.domain.enums.messenger_type import MessengerType
from src.messaging.domain.entities.session import Session
from src.messaging.ports.messengers.base import AbstractMessenger
from src.messaging.ports.messengers.descriptor import (
    MessengerDescriptor,
    describe_messenger,
)


class MessengerRegistry:
    """Registry for messenger instances."""

    def __init__(
        self, messengers: dict[MessengerType, AbstractMessenger] | None = None
    ) -> None:
        self._messengers = messengers or {}

    def describe_all(self) -> list[MessengerDescriptor]:
        return [
            describe_messenger(messenger_type, messenger)
            for messenger_type, messenger in self._messengers.items()
        ]

    def get_messenger(self, messenger_type: MessengerType) -> AbstractMessenger:
        messenger = self._messengers.get(messenger_type)
        if messenger is None:
            raise ValueError(f"No messenger registered for {messenger_type}")
        return messenger

    async def for_session(self, session: Session) -> AbstractMessenger:
        messenger = self.get_messenger(session.session_type)
        await messenger.set_session(session)
        return messenger
