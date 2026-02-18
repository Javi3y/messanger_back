from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.messaging.adapters.sqlalchemydb.models.messaging_request import (
    MessagingRequestModel,
)
from src.messaging.domain.entities.messaging_request import MessagingRequest
from src.messaging.ports.repositories.messaging_request_repo_port import (
    MessagingRequestRepositoryPort,
)


class SqlalchemyMessagingRequestRepository(
    AsyncSqlalchemyRepository[MessagingRequest, MessagingRequestModel],
    MessagingRequestRepositoryPort,
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MessagingRequestModel)

    async def get_not_generated(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
        lock: bool = False,
        skip_locked: bool = False,
        **kwargs,
    ) -> list[MessagingRequest]:
        stmt = (
            select(MessagingRequestModel)
            .where(MessagingRequestModel.generated.is_(False))
            .order_by(MessagingRequestModel.id.asc())
            .offset(offset)
            .limit(limit)
        )

        if not include_deleted:
            stmt = stmt.where(MessagingRequestModel.deleted_at.is_(None))

        if lock:
            stmt = stmt.with_for_update(skip_locked=skip_locked)

        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]
