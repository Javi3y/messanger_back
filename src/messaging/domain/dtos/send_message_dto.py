from src.base.domain.dto import BaseDTO
from src.messaging.domain.dtos.message_dto import MessageDTO
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO


class SendMessageDTO(BaseDTO):
    def __init__(self, *, message: MessageDTO, message_request: MessageRequestDTO):
        self.message = message
        self.message_request = message_request
