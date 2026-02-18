from abc import ABC, abstractmethod
from typing import Any

from src.base.ports.database import AsyncDatabase

from src.messaging.ports.queries.messaging_queries_port import (
    MessagingQueriesPort,
)

import src.users.ports.repositories as user_repos
import src.files.ports.repositories as file_repos
import src.messaging.ports.repositories as messaging_repos
from src.base.ports.repositories.outbox_event_repo_port import OutboxEventRepositoryPort


class AsyncUnitOfWork(ABC):
    def __init__(self, database: AsyncDatabase) -> None:
        self.database = database
        self.session: Any | None = None
        self._session_cm: Any | None = None

        # repos (types)
        self.base_user_repo: user_repos.BaseUserRepositoryPort
        self.admin_repo: user_repos.AdminRepositoryPort
        self.user_repo: user_repos.UserRepositoryPort

        self.file_repo: file_repos.FileRepositoryPort

        self.session_repo: messaging_repos.SessionRepositoryPort
        self.message_request_repo: messaging_repos.MessagingRequestRepositoryPort
        self.message_repo: messaging_repos.MessageRepositoryPort

        self.outbox_event_repo: OutboxEventRepositoryPort

        # queries (types)
        self.messaging_queries: MessagingQueriesPort

    async def __aenter__(self):
        self._session_cm = self.database.get_session()
        self.session = await self._session_cm.__aenter__()
        await self._init_repositories()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session_cm:
            return

        try:
            if exc_type:
                await self.rollback()
        finally:
            await self._session_cm.__aexit__(exc_type, exc_val, exc_tb)
            self._session_cm = None
            self.session = None

    @abstractmethod
    async def _init_repositories(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None: ...
    @abstractmethod
    async def flush(self) -> None: ...
    @abstractmethod
    async def rollback(self) -> None: ...
