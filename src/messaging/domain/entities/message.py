from datetime import UTC, datetime

from src.base.domain.entity import BaseEntity
from src.messaging.domain.enums.message_status import MessageStatus


class Message(BaseEntity):
    repo_attr = "message_repo"

    message_request_id: int
    sending_time: datetime
    sent_time: datetime | None
    text: str
    phone_number: str | None
    username: str | None
    user_id: str | None
    attachment_file_id: int | None
    status: MessageStatus
    error_message: str | None

    def __init__(
        self,
        *,
        message_request_id: int,
        text: str,
        sending_time: datetime | None = None,
        sent_time: datetime | None = None,
        phone_number: str | None = None,
        username: str | None = None,
        user_id: str | None = None,
        attachment_file_id: int | None = None,
        status: MessageStatus = MessageStatus.pending,
        error_message: str | None = None,
        id: int | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id, deleted_at=deleted_at)
        self.message_request_id = message_request_id
        self.sending_time = sending_time or datetime.now(UTC)
        self.sent_time = sent_time
        self.text = text
        self.phone_number = phone_number
        self.username = username
        self.user_id = user_id
        self.attachment_file_id = attachment_file_id
        self.status = status
        self.error_message = error_message
