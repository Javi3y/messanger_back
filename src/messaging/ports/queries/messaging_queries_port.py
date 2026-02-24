from abc import ABC, abstractmethod

from src.base.ports.queries.queries import AbstractQueries
from src.messaging.domain.dtos.message_dto import MessageDTO
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO
from src.messaging.domain.dtos.session_dto import SessionDTO


class MessagingQueriesPort(AbstractQueries, ABC):
    @abstractmethod
    async def get_request_details(
        self,
        *,
        request_id: int,
    ) -> MessageRequestDTO | None:
        raise NotImplementedError

    @abstractmethod
    async def get_messages_for_request(
        self,
        *,
        request_id: int,
    ) -> list[MessageDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_session_details(
        self,
        *,
        session_id: int,
    ) -> SessionDTO | None:
        raise NotImplementedError
