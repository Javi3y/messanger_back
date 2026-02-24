from src.base.domain.dto import BaseDTO


class CreateMessageRequestImportDTO(BaseDTO):
    def __init__(self, *, message_request_id: int, job_key: str):
        self.message_request_id = message_request_id
        self.job_key = job_key
