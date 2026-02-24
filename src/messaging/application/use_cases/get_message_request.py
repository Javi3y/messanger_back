from src.base.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO
from src.messaging.domain.entities.messaging_request import MessagingRequest
from src.users.domain.entities.base_user import BaseUser


async def get_message_request_use_case(
    *,
    message_request_id: int,
    user: BaseUser,
    uow: AsyncUnitOfWork,
) -> MessageRequestDTO:
    if user.id is None:
        raise BadRequestException(detail="User id is required")
    current_user_id = int(user.id)

    request = await uow.messaging_queries.get_request_details(
        request_id=message_request_id
    )
    if not request:
        raise NotFoundException(entity=MessagingRequest)

    if request.user.id != current_user_id:
        raise ForbiddenException(
            detail="You do not have access to this message request"
        )

    return request
