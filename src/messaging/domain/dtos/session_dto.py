from src.base.domain.dto import BaseDTO


class SessionDTO(BaseDTO):
    def __init__(
        self,
        *,
        id: int,
        title: str,
        phone_number: str | None,
        session_type: str,
        is_active: bool,
        user_id: int,
    ):
        self.id = id
        self.title = title
        self.phone_number = phone_number
        self.session_type = session_type
        self.is_active = is_active
        self.user_id = user_id
