from datetime import UTC, datetime

from src.base.domain.entity import BaseEntity


class MessagingRequest(BaseEntity):
    repo_attr = "message_request_repo"

    user_id: int
    title: str | None
    session_id: int
    request_file_id: int | None = None
    attachment_file_id: int | None = None
    sending_time: datetime
    default_text: str | None = None

    def __init__(
        self,
        *,
        user_id: int,
        session_id: int,
        request_file_id: int | None = None,
        attachment_file_id: int | None = None,
        title: str | None = None,
        sending_time: datetime | None = None,
        default_text: str | None = None,
        id: int | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id, deleted_at=deleted_at)
        self.user_id = user_id
        self.title = title
        self.session_id = session_id
        self.request_file_id = request_file_id
        self.attachment_file_id = attachment_file_id
        self.sending_time = sending_time or datetime.now(UTC)
        self.default_text = default_text
