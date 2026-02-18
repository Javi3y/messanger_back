from src.base.exceptions import NotFoundException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO
from src.messaging.domain.entities.messaging_request import MessagingRequest


async def get_message_request_use_case(
    *,
    message_request_id: int,
    uow: AsyncUnitOfWork,
) -> MessageRequestDTO:
    request = await uow.messaging_queries.get_request_details(
        request_id=message_request_id
    )
    if not request:
        raise NotFoundException(entity=MessagingRequest)
    return request
