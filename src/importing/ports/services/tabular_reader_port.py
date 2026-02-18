from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class TabularRow:
    row_number: int
    values: dict[str, Any]  # header -> value


@dataclass(frozen=True)
class TabularDocument:
    headers: list[str]
    rows: Iterable[TabularRow]


class TabularReaderPort(ABC):
    @abstractmethod
    def can_read(self, *, filename: str | None, content_type: str | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def read(
        self, *, filename: str | None, content_type: str | None, content: bytes
    ) -> TabularDocument:
        raise NotImplementedError
