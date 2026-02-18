from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator


class AsyncDatabase(ABC):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @abstractmethod
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Any, None]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
