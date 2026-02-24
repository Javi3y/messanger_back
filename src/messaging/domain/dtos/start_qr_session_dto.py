from src.base.domain.dto import BaseDTO
from src.files.domain.dtos.file_dto import FileDTO
from src.messaging.domain.dtos.session_dto import SessionDTO


class StartQrSessionDTO(BaseDTO):
    def __init__(self, *, session: SessionDTO, file: FileDTO):
        self.session = session
        self.file = file
