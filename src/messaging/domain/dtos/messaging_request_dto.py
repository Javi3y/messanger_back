from datetime import datetime

from src.base.domain.dto import BaseDTO
from src.files.domain.dtos.file_dto import FileDTO
from src.users.domain.dtos.user_dto import UserDTO


class MessageRequestDTO(BaseDTO):
    """
    Data Transfer Object for MessagingRequest entities.

    Includes nested User and CSV File.
    """

    def __init__(
        self,
        id: int,
        user: UserDTO,
        session_id: int,
        csv_file: FileDTO | None = None,
        attachment_file: FileDTO | None = None,
        title: str | None = None,
        default_text: str | None = None,
        sending_time: datetime | None = None,
    ):
        self.id = id
        self.user = user  # Nested UserDTO
        self.session_id = session_id
        self.csv_file = csv_file  # Nested FileDTO (CSV file)
        self.attachment_file = attachment_file  # Nested FileDTO (attachment)
        self.title = title
        self.default_text = default_text
        self.sending_time = sending_time
