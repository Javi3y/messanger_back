from src.base.domain.dto import BaseDTO
from src.users.domain.dtos.user_dto import UserDTO


class SessionDTO(BaseDTO):
    def __init__(
        self,
        *,
        id: int,
        title: str,
        phone_number: str | None,
        session_type: str,
        is_active: bool,
        user: UserDTO,
    ):
        self.id = id
        self.title = title
        self.phone_number = phone_number
        self.session_type = session_type
        self.is_active = is_active
        self.user = user
