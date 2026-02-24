from src.base.domain.dto import BaseDTO
from src.messaging.domain.dtos.message_dto import MessageDTO
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO


class SendMessageDTO(MessageDTO):
    def __init__(self, *, message_request: MessageRequestDTO, **kwargs):
        super().__init__(**kwargs)
        self.message_request = message_request
