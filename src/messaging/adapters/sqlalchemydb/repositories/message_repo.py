from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.messaging.adapters.sqlalchemydb.models.message import MessageModel
from src.messaging.domain.enums.message_status import MessageStatus
from src.messaging.domain.entities.message import Message
from src.messaging.ports.repositories.message_repo_port import (
    MessageRepositoryPort,
)


class SqlalchemyMessageRepository(
    AsyncSqlalchemyRepository[Message, MessageModel],
    MessageRepositoryPort,
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=MessageModel)

    async def get_pending_to_send_before(
        self,
        *,
        before: datetime,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
        lock: bool = False,
        skip_locked: bool = True,
        **kwargs,
    ) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(
                MessageModel.status == MessageStatus.pending,
                MessageModel.sending_time <= before,
                MessageModel.sent_time.is_(None),
            )
            .order_by(MessageModel.sending_time.asc(), MessageModel.id.asc())
            .offset(offset)
            .limit(limit)
        )

        if not include_deleted:
            stmt = stmt.where(MessageModel.deleted_at.is_(None))

        if lock:
            stmt = stmt.with_for_update(skip_locked=skip_locked)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_pending_for_request_to_send_before(
        self,
        *,
        request_id: int,
        before: datetime,
        limit: int = 100,
        lock: bool = False,
        skip_locked: bool = True,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(
                MessageModel.message_request_id == request_id,
                MessageModel.status == MessageStatus.pending,
                MessageModel.sending_time <= before,
                MessageModel.sent_time.is_(None),
            )
            .order_by(MessageModel.sending_time.asc(), MessageModel.id.asc())
            .limit(limit)
        )

        if not include_deleted:
            stmt = stmt.where(MessageModel.deleted_at.is_(None))

        if lock:
            stmt = stmt.with_for_update(skip_locked=skip_locked)

        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]

    async def get_next_pending_sending_time_for_request(
        self,
        *,
        request_id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> datetime | None:
        stmt = (
            select(MessageModel.sending_time)
            .where(
                MessageModel.message_request_id == request_id,
                MessageModel.status == MessageStatus.pending,
                MessageModel.sent_time.is_(None),
            )
            .order_by(MessageModel.sending_time.asc(), MessageModel.id.asc())
            .limit(1)
        )

        if not include_deleted:
            stmt = stmt.where(MessageModel.deleted_at.is_(None))

        res = await self.session.execute(stmt)
        return res.scalars().first()
