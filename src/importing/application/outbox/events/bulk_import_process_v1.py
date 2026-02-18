from dataclasses import dataclass
from typing import Any

from src.base.domain.events.outbox_domain_event import OutboxDomainEvent


@dataclass(kw_only=True, frozen=True)
class BulkImportProcessV1(OutboxDomainEvent):
    TYPE = "bulk_import.process.v1"

    job_key: str
    import_type: str
    batch_size: int
    ttl_seconds: int
    context: dict[str, Any]
