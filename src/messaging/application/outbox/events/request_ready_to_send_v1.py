from dataclasses import dataclass
from typing import ClassVar

from src.base.domain.events.outbox_domain_event import OutboxDomainEvent


@dataclass(frozen=True)
class MessageRequestReadyToSendV1(OutboxDomainEvent):
    TYPE: ClassVar[str] = "messaging.request_ready_to_send.v1"

    message_request_id: int
