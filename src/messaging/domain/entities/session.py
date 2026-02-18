from datetime import datetime
from uuid import UUID, uuid4

from src.base.domain.entity import BaseEntity
from src.messaging.domain.enums.messenger_type import MessengerType


class Session(BaseEntity):
    repo_attr = "session_repo"

    user_id: int
    title: str
    uuid: UUID | None
    phone_number: str
    session_type: MessengerType
    session_str: str | None = None
    is_active: bool = False

    def __init__(
        self,
        *,
        user_id: int,
        title: str,
        phone_number: str,
        session_type: MessengerType,
        session_str: str | None = None,
        id: int | None = None,
        uuid: UUID | None = None,
        deleted_at: datetime | None = None,
        is_active: bool = False,
    ) -> None:
        super().__init__(id, deleted_at)

        self.user_id = user_id
        self.title = title
        self.phone_number = phone_number
        self.session_type = session_type
        self.session_str = session_str
        self.uuid = uuid
        self.is_active = is_active

        if session_type == MessengerType.whatsapp:
            # WhatsApp uses uuid, must NOT use session_str
            if self.uuid is None:
                self.uuid = uuid4()
            if self.session_str is not None:
                raise ValueError(
                    "WhatsApp messenger should not have a session_str (it uses uuid instead)"
                )

        elif session_type == MessengerType.telegram:
            # Telegram uses session_str, must NOT use uuid
            if self.uuid is not None:
                raise ValueError("Telegram should not have uuid")
            if not self.session_str:
                raise ValueError(
                    "Telegram messenger should have a session_str (login session)"
                )
            self.uuid = None
