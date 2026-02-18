from dataclasses import dataclass
from typing import Any

from src.base.domain.events.outbox_domain_event import OutboxDomainEvent


@dataclass(kw_only=True, frozen=True)
class BulkImportStageV1(OutboxDomainEvent):
    TYPE = "bulk_import.stage.v1"

    job_key: str
    import_type: str
    file_id: int
    ttl_seconds: int
    config: dict[str, Any]
    context: dict[str, Any]
