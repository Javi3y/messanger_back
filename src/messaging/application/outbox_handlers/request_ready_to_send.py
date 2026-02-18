import logging
from datetime import datetime, timezone

from src.base.application.services.outbox_service import OutboxService
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.application.outbox.events.request_ready_to_send_v1 import (
    MessageRequestReadyToSendV1,
)
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.messaging.domain.entities.contact import Contact
from src.messaging.domain.enums.message_status import MessageStatus
from src.messaging.domain.validators.contact_validator import (
    validate_contact_for_messenger,
)

logger = logging.getLogger(__name__)

SEND_BATCH = 50


async def handle_request_ready_to_send(
    *,
    uow: AsyncUnitOfWork,
    event: MessageRequestReadyToSendV1,
    messenger_registry: MessengerRegistry,
) -> None:
    if event is None:
        raise RuntimeError("Typed event not registered for this handler")

    now = datetime.now(timezone.utc)

    req = await uow.message_request_repo.get_by_id(id=event.message_request_id)
    if req is None:
        raise RuntimeError(f"MessageRequest not found: {event.message_request_id}")

    session = await uow.session_repo.get_by_id(id=req.session_id)
    if session is None:
        raise RuntimeError(f"Session not found: {req.session_id}")

    # lock a batch of due messages
    messages = await uow.message_repo.get_pending_to_send_before(
        before=now,
        limit=SEND_BATCH,
        lock=True,
        skip_locked=True,
    )

    # only send messages belonging to this request (cheap filter)
    messages = [m for m in messages if m.message_request_id == req.id]

    if not messages:
        return

    messenger = await messenger_registry.for_session(session)

    sent_any = 0
    for msg in messages:
        try:
            validate_contact_for_messenger(
                phone_number=msg.phone_number,
                username=msg.username,
                user_id=msg.user_id,
                messenger_type=session.session_type,
            )

            file = (
                await uow.file_repo.get_by_id(id=msg.attachment_file_id)
                if msg.attachment_file_id
                else None
            )

            contact = Contact(
                contact_type=session.session_type,
                phone_number=msg.phone_number,
                username=msg.username,
                id=msg.user_id,
            )

            await messenger.send_message(contact=contact, text=msg.text, file=file)

            msg.status = MessageStatus.successful
            msg.sent_time = now
            await uow.message_repo.update(entity=msg)
            sent_any += 1

        except Exception as e:
            logger.exception("Failed sending message id=%s", getattr(msg, "id", None))
            msg.status = MessageStatus.failed
            msg.error_message = str(e)[:500]
            await uow.message_repo.update(entity=msg)

    # If we sent something, check if more remain; if so re-enqueue quickly.
    if sent_any > 0:
        remaining = await uow.message_repo.get_pending_to_send_before(
            before=now,
            limit=1,
            lock=False,
            skip_locked=True,
        )
        remaining = [m for m in remaining if m.message_request_id == req.id]
        if remaining:
            outbox = OutboxService(uow)
            await outbox.publish(
                MessageRequestReadyToSendV1(
                    message_request_id=req.id,
                    available_at=now,  # immediate retry for next batch
                    dedup_key=f"messaging_request:{req.id}:send",
                    aggregate_type="messaging_request",
                    aggregate_id=str(req.id),
                )
            )
