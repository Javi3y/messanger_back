from datetime import UTC, datetime

from src.base.application.services.outbox_service import OutboxService
from src.base.exceptions import BadRequestException, NotFoundException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.application.outbox.events.request_ready_to_send_v1 import (
    MessageRequestReadyToSendV1,
)
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO
from src.messaging.domain.dtos.send_message_dto import SendMessageDTO
from src.messaging.domain.entities.message import Message, MessageStatus
from src.messaging.domain.entities.messaging_request import MessagingRequest
from src.messaging.domain.validators.contact_validator import (
    validate_contact_for_messenger,
)
from src.users.domain.entities.base_user import BaseUser


async def send_message_use_case(
    *,
    session_id: int,
    phone_number: str | None,
    username: str | None,
    user_id: str | None,
    text: str,
    file_id: int | None,
    current_user: BaseUser,
    uow: AsyncUnitOfWork,
) -> SendMessageDTO:
    # Get session to validate contact data matches messenger type
    session = await uow.session_repo.get_by_id(id=session_id)
    if session is None:
        raise BadRequestException(f"Session not found: {session_id}")
    if session.id is None:
        raise BadRequestException("Session id is required")
    session_entity_id = int(session.id)
    if current_user.id is None:
        raise BadRequestException("User id is required")
    current_user_id = int(current_user.id)

    # Validate contact data before creating the message
    validate_contact_for_messenger(
        phone_number=phone_number,
        username=username,
        user_id=user_id,
        messenger_type=session.session_type,
    )

    # Create message request
    message_request = MessagingRequest(
        user_id=current_user_id,
        session_id=session_entity_id,
        request_file_id=None,
        attachment_file_id=file_id,
        title=None,
        default_text=text,
    )
    message_request = await uow.message_request_repo.add(entity=message_request)
    await uow.flush()
    if message_request.id is None:
        raise BadRequestException("Message request id is required")
    message_request_id = int(message_request.id)

    # Create message entity with status=pending and sending_time=now
    # The worker will pick this up and send it
    msg = Message(
        message_request_id=message_request_id,
        text=text,
        phone_number=phone_number,
        username=username,
        user_id=user_id,
        attachment_file_id=file_id,
        sending_time=datetime.now(UTC),
        status=MessageStatus.pending,
    )
    msg = await uow.message_repo.add(entity=msg)
    await uow.flush()
    if msg.id is None:
        raise BadRequestException("Message id is required")
    message_id = int(msg.id)

    # enqueue outbox event for request-level sending
    outbox = OutboxService(uow)
    await outbox.publish(
        MessageRequestReadyToSendV1(
            message_request_id=message_request_id,
            available_at=msg.sending_time,
            dedup_key=f"messaging_request:{message_request_id}:send",
            aggregate_type="messaging_request",
            aggregate_id=str(message_request_id),
        )
    )

    dto = await uow.messaging_queries.get_request_details(request_id=message_request_id)
    if dto is None:
        raise NotFoundException(entity=MessagingRequest)

    message_dto = await uow.messaging_queries.get_message_by_id(message_id=message_id)
    if message_dto is None:
        raise NotFoundException(entity=Message)

    return SendMessageDTO(message=message_dto, message_request=dto)
