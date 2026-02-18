from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CacheEntry:
    key: str
    value: Any
    ttl: int | None = None
    created_at: datetime = utc_now()

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = utc_now()

    @property
    def expires_at(self) -> datetime | None:
        if self.ttl is None:
            return None
        return self.created_at + timedelta(seconds=self.ttl)
