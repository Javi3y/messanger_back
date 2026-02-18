from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.base.adapters.sqlalchemydb.models.outbox_event import OutboxEventModel
from src.base.domain.entities.outbox_event import OutboxEvent
from src.base.ports.repositories.outbox_event_repo_port import OutboxEventRepositoryPort


class SqlalchemyOutboxEventRepository(
    AsyncSqlalchemyRepository[OutboxEvent, OutboxEventModel],
    OutboxEventRepositoryPort,
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=OutboxEventModel)

    async def get_ready(
        self,
        *,
        now: datetime,
        limit: int = 100,
        lock: bool = False,
        skip_locked: bool = True,
        **kwargs,
    ) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEventModel)
            .where(
                OutboxEventModel.processed_at.is_(None),
                OutboxEventModel.available_at <= now,
            )
            .order_by(OutboxEventModel.available_at.asc(), OutboxEventModel.id.asc())
            .limit(limit)
        )

        if lock:
            stmt = stmt.with_for_update(skip_locked=skip_locked)

        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]
