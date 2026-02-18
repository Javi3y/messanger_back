from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar, Self
from abc import ABC

from src.base.domain.dto import BaseDTO


@dataclass(frozen=True, kw_only=True)
class OutboxDomainEvent(BaseDTO, ABC):
    TYPE: ClassVar[str]

    # persisted on the OutboxEvent row (not inside payload)
    available_at: datetime | None = None
    dedup_key: str | None = None
    aggregate_type: str | None = None
    aggregate_id: str | None = None

    # BaseDTO.dump honors this
    __serialize_exclude__: ClassVar[set[str]] = {
        "available_at",
        "dedup_key",
        "aggregate_type",
        "aggregate_id",
    }

    @classmethod
    def event_type(cls) -> str:
        return cls.TYPE

    def payload(self) -> dict[str, Any]:
        # BaseDTO.dump exists in your project and supports exclude_none
        return self.dump(exclude_none=True)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        # relies on subclasses having __init__ matching payload keys
        return cls(**payload)  # type: ignore[arg-type]

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)
