"""
Message DTO.
"""

from datetime import datetime

from src.base.domain.dto import BaseDTO
from src.messaging.domain.enums.message_status import MessageStatus


class MessageDTO(BaseDTO):

    def __init__(
        self,
        id: int,
        message_request_id: int,
        text: str,
        phone_number: str | None = None,
        username: str | None = None,
        user_id: str | None = None,
        attachment_file_id: int | None = None,
        sending_time: datetime | None = None,
        sent_time: datetime | None = None,
        status: MessageStatus = MessageStatus.pending,
        error_message: str | None = None,
    ):
        self.id = id
        self.message_request_id = message_request_id
        self.text = text
        self.phone_number = phone_number
        self.username = username
        self.user_id = user_id
        self.attachment_file_id = attachment_file_id
        self.sending_time = sending_time
        self.sent_time = sent_time
        self.status = status
        self.error_message = error_message
