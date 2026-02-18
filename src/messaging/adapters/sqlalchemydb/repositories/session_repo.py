from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.messaging.adapters.sqlalchemydb.models.session import SessionModel
from src.messaging.domain.entities.session import Session, MessengerType
from src.messaging.ports.repositories.session_repo_port import (
    SessionRepositoryPort,
)


class SqlalchemySessionRepository(
    AsyncSqlalchemyRepository[Session, SessionModel],
    SessionRepositoryPort,
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SessionModel)

    async def get_by_uuid(
        self,
        *,
        uuid: UUID,
        include_deleted: bool = False,
        **kwargs,
    ) -> Session | None:
        stmt = select(SessionModel).where(SessionModel.uuid == uuid)
        if not include_deleted:
            stmt = stmt.where(SessionModel.deleted_at.is_(None))

        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_active_by_phone_and_type(
        self,
        *,
        phone_number: str,
        session_type: MessengerType,
        include_deleted: bool = False,
        **kwargs,
    ) -> Session | None:
        stmt = select(SessionModel).where(
            SessionModel.phone_number == phone_number,
            SessionModel.session_type == session_type,
            SessionModel.is_active.is_(True),
        )
        if not include_deleted:
            stmt = stmt.where(SessionModel.deleted_at.is_(None))

        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None
