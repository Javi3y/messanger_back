from collections.abc import Callable
from typing import Any

from src.base.domain.events.outbox_domain_event import OutboxDomainEvent
from src.importing.application.outbox.events.bulk_import_process_v1 import (
    BulkImportProcessV1,
)
from src.importing.application.outbox.events.bulk_import_stage_v1 import (
    BulkImportStageV1,
)
from src.importing.application.outbox_handlers.bulk_import_process import (
    handle_bulk_import_process_v1,
)
from src.importing.application.outbox_handlers.bulk_import_stage import (
    handle_bulk_import_stage_v1,
)
from src.messaging.application.outbox.events.request_ready_to_send_v1 import (
    MessageRequestReadyToSendV1,
)
from src.messaging.application.outbox_handlers.request_ready_to_send import (
    handle_request_ready_to_send,
)


class OutboxRegistry:
    def __init__(self):
        self.handlers: dict[str, Callable] = {}
        self.event_classes: dict[str, type[OutboxDomainEvent]] = {}
        self.register(
            MessageRequestReadyToSendV1.event_type(),
            handle_request_ready_to_send,
            MessageRequestReadyToSendV1,
        )
        self.register(
            BulkImportStageV1.event_type(),
            handle_bulk_import_stage_v1,
            BulkImportStageV1,
        )
        self.register(
            BulkImportProcessV1.event_type(),
            handle_bulk_import_process_v1,
            BulkImportProcessV1,
        )

    def register(
        self,
        event_type: str,
        handler: Callable,
        event_cls: type[OutboxDomainEvent] | None = None,
    ):
        self.handlers[event_type] = handler
        if event_cls:
            self.event_classes[event_type] = event_cls

    def get_handler(self, event_type: str) -> Callable | None:
        return self.handlers.get(event_type)

    def build_event(
        self, event_type: str, payload: dict[str, Any]
    ) -> OutboxDomainEvent | None:
        event_cls = self.event_classes.get(event_type)
        return event_cls.from_payload(payload) if event_cls else None
