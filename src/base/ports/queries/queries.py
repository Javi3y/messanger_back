from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass
class QueryParams:

    offset: int
    limit: int


class AbstractQueries(ABC):
    def __init__(self, session: Any) -> None:
        self.session = session
