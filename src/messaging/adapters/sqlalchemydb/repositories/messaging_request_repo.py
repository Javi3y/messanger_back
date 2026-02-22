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
