from src.base.domain.dto import BaseDTO


class StartOtpSessionDTO(BaseDTO):
    def __init__(self, *, session_id: int, message: str):
        self.session_id = session_id
        self.message = message
