from datetime import datetime, timezone
from typing import Any

from src.base.domain.entity import BaseEntity


class OutboxEvent(BaseEntity):

    repo_attr = "outbox_event_repo"

    event_type: str
    payload: dict[str, Any]

    # when the dispatcher is allowed to process it
    available_at: datetime

    # set when successfully processed OR dead-lettered
    processed_at: datetime | None

    # retry bookkeeping
    attempts: int
    last_error: str | None

    # optional future-proofing fields (helpful for dedupe/streaming later)
    dedup_key: str | None
    aggregate_type: str | None
    aggregate_id: str | None

    created_at: datetime

    def __init__(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
        available_at: datetime | None = None,
        processed_at: datetime | None = None,
        attempts: int = 0,
        last_error: str | None = None,
        dedup_key: str | None = None,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        created_at: datetime | None = None,
        id: int | None = None,
    ) -> None:
        super().__init__(id=id, deleted_at=None)
        now = datetime.now(timezone.utc)

        self.event_type = event_type
        self.payload = payload

        self.available_at = available_at or now
        self.processed_at = processed_at

        self.attempts = attempts
        self.last_error = last_error

        self.dedup_key = dedup_key
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id

        self.created_at = created_at or now
