from datetime import datetime

from app.schemas.base import AbstractBaseModel
from app.v1.files.schemas.v1_responses import V1FileResponse
from app.v1.users.schemas.v1_responses import V1BaseUserResponse
from src.messaging.domain.enums.message_status import MessageStatus


class V1MessengerDescriptorResponse(AbstractBaseModel):
    type: str
    display_name: str
    features: set[str]
    auth_methods: set[str]
    contact_identifiers: set[str]


class V1SessionResponse(AbstractBaseModel):
    id: int
    title: str
    phone_number: str | None = None
    session_type: str
    is_active: bool
    user: V1BaseUserResponse


class V1MessageResponse(AbstractBaseModel):
    id: int
    message_request_id: int
    text: str
    phone_number: str | None = None
    username: str | None = None
    sending_time: datetime | None = None
    sent_time: datetime | None = None
    status: MessageStatus
    error_message: str | None = None


class V1StartOtpSessionResponse(AbstractBaseModel):
    session_id: int
    message: str


class V1CreateMessageRequestImportResponse(AbstractBaseModel):
    message_request_id: int
    job_key: str


class V1StartQrSessionResponse(AbstractBaseModel):
    session: V1SessionResponse
    file: V1FileResponse


class V1QrCodeResponse(AbstractBaseModel):
    qr_code: str


class V1MessageRequestResponse(AbstractBaseModel):
    id: int
    user: V1BaseUserResponse
    session_id: int
    csv_file: V1FileResponse | None = None
    attachment_file: V1FileResponse | None = None
    title: str | None = None
    default_text: str | None = None
    sending_time: datetime | None = None


class V1SendMessageResponse(AbstractBaseModel):
    id: int
    message_request_id: int
    text: str
    phone_number: str | None = None
    username: str | None = None
    sending_time: datetime | None = None
    sent_time: datetime | None = None
    status: MessageStatus
    error_message: str | None = None
    message_request: V1MessageRequestResponse
