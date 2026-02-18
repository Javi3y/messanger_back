"""
Create messaging request from CSV use case.

Creates a MessagingRequest entity from a CSV file upload, with optional
defaults for message content, sending time, and attachments.
"""

from datetime import datetime, timezone

from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.application.use_cases.get_file import get_file_service
from src.files.ports.services.file_service import FileServicePort
from src.messaging.domain.entities.messaging_request import MessagingRequest


async def create_messaging_request_from_csv_use_case(
    *,
    session_id: int,
    file_id: int,
    title: str | None,
    default_text: str | None,
    default_sending_time: datetime | None,
    attachment_file_id: int | None,
    user_id: int,
    uow: AsyncUnitOfWork,
    file_service: FileServicePort,
) -> MessagingRequest:
    # Retrieve the CSV file
    stored_file = await get_file_service(uow=uow, file_service=file_service, id=file_id)

    # Create the messaging request entity
    req = MessagingRequest(
        user_id=user_id,
        session_id=session_id,
        request_file_id=stored_file.id,
        title=title,
        default_text=default_text,
        attachment_file_id=attachment_file_id,
        sending_time=default_sending_time or datetime.now(timezone.utc),
        generated=False,
    )
    req = await uow.message_request_repo.add(entity=req)

    return req
