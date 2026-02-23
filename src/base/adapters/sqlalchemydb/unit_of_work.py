from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.base.adapters.sqlalchemydb.database import AsyncSqlalchemyDatabase
from src.base.ports.repositories.cache_repository import AbstractCacheRepository

from src.messaging.adapters.sqlalchemydb.queries.messaging_queries import (
    SqlalchemyMessagingQueries,
)
from src.files.adapters.sqlalchemydb.queries.file_queries import SqlalchemyFileQueries

import src.users.adapters.sqlalchemydb.repositories as user_repos
import src.files.adapters.sqlalchemydb.repositories as file_repos
import src.messaging.adapters.sqlalchemydb.repositories as messaging_repos
import src.base.adapters.sqlalchemydb.repositories as base_repos


class AsyncSqlalchemyUnitOfWork(AsyncUnitOfWork):
    def __init__(
        self,
        database: AsyncSqlalchemyDatabase,
        cache_repo: Optional[AbstractCacheRepository] = None,
    ) -> None:
        super().__init__(database)
        self._cache_repo = cache_repo
        self.session: AsyncSession | None = None

    async def _init_repositories(self) -> None:
        assert self.session is not None

        # user repos (no caching - domain entities should not be cached)
        self.base_user_repo = user_repos.SqlalchemyBaseUserRepository(
            self.session, cache_repo=None
        )
        self.admin_repo = user_repos.SqlalchemyAdminRepository(
            self.session, cache_repo=None
        )
        self.user_repo = user_repos.SqlalchemyUserRepository(
            self.session, cache_repo=None
        )

        # file repos (without caching for now)
        self.file_repo = file_repos.SqlalchemyFileRepository(self.session)

        # messaging repos (without caching for now)
        self.session_repo = messaging_repos.SqlalchemySessionRepository(self.session)
        self.message_request_repo = (
            messaging_repos.SqlalchemyMessagingRequestRepository(self.session)
        )
        self.message_repo = messaging_repos.SqlalchemyMessageRepository(self.session)

        # base repos (outbox, etc.)
        self.outbox_event_repo = base_repos.SqlalchemyOutboxEventRepository(
            self.session
        )

        # messaging queries (read-side)
        self.file_queries = SqlalchemyFileQueries(self.session)
        self.messaging_queries = SqlalchemyMessagingQueries(self.session)

    async def commit(self) -> None:
        if self.session:
            await self.session.commit()

    async def flush(self) -> None:
        if self.session:
            await self.session.flush()

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()
