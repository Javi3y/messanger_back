from datetime import UTC, datetime

from src.base.application.services.outbox_service import OutboxService
from src.base.exceptions import BadRequestException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.application.outbox.events.request_ready_to_send_v1 import (
    MessageRequestReadyToSendV1,
)
from src.messaging.domain.entities.message import Message, MessageStatus
from src.messaging.domain.entities.messaging_request import MessagingRequest
from src.messaging.domain.validators.contact_validator import (
    validate_contact_for_messenger,
)


async def send_message_use_case(
    *,
    session_id: int,
    phone_number: str | None,
    username: str | None,
    user_id: str | None,
    text: str,
    file_id: int | None,
    current_user_id: int,
    uow: AsyncUnitOfWork,
) -> tuple[int, int]:
    """
    Create a pending message that will be sent by the background worker.

    The outbox pattern ensures transactional consistency:
    1. Message is created with status=pending and sending_time=now
    2. Endpoint commits transaction
    3. Worker picks up the message and sends it
    4. Worker updates status to successful/failed

    This prevents the "impossible state" where a message is sent
    successfully but the DB transaction fails to commit.

    Args:
        session_id: The session to use for sending
        phone_number: Contact's phone number
        username: Contact's username (for Telegram)
        user_id: Contact's ID (for Telegram)
        text: Message text
        file_id: Optional attachment file ID
        current_user_id: ID of the user sending the message
        uow: Unit of Work for database operations (endpoint owns the transaction)

    Returns:
        Tuple of (message_request_id, message_id)
    """
    # Get session to validate contact data matches messenger type
    session = await uow.session_repo.get_by_id(id=session_id)
    if session is None:
        raise BadRequestException(f"Session not found: {session_id}")

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
        session_id=session.id,
        request_file_id=None,
        attachment_file_id=file_id,
        title=None,
        default_text=text,
    )
    message_request = await uow.message_request_repo.add(entity=message_request)
    await uow.flush()

    # Create message entity with status=pending and sending_time=now
    # The worker will pick this up and send it
    msg = Message(
        message_request_id=message_request.id,
        text=text,
        phone_number=phone_number,
        username=username,
        user_id=user_id,
        attachment_file_id=file_id,
        sending_time=datetime.now(UTC),
        status=MessageStatus.pending,
    )
    msg = await uow.message_repo.add(entity=msg)

    # enqueue outbox event for request-level sending
    outbox = OutboxService(uow)
    await outbox.publish(
        MessageRequestReadyToSendV1(
            message_request_id=message_request.id,
            available_at=msg.sending_time,
            dedup_key=f"messaging_request:{message_request.id}:send",
            aggregate_type="messaging_request",
            aggregate_id=str(message_request.id),
        )
    )

    return message_request.id, msg.id
