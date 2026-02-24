from datetime import datetime

from pydantic import ConfigDict

from app.schemas.base import AbstractBaseModel
from src.messaging.application.import_handlers.message_request_import_config import (
    MessageRequestImportConfig,
)
from src.messaging.domain.enums.messenger_type import MessengerType


class V1StartOtpSessionRequest(AbstractBaseModel):
    messenger_type: MessengerType
    title: str
    phone_number: str


class V1StartQrSessionRequest(AbstractBaseModel):
    messenger_type: MessengerType
    title: str
    phone_number: str


class V1TelegramOtpRequest(AbstractBaseModel):
    session_id: int
    otp: int


class V1TelegramPasswordRequest(AbstractBaseModel):
    session_id: int
    password: str


class V1ContactModel(AbstractBaseModel):
    username: str | None = None
    id: str | None = None
    phone_number: str | None = None


class V1MessageRequest(AbstractBaseModel):
    session_id: int
    contact: V1ContactModel
    text: str
    file_id: int | None = None


class V1ImportMessageRequest(AbstractBaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: int
    file_id: int
    title: str | None = None
    default_text: str | None = None
    default_sending_time: datetime | None = None
    attachment_file_id: int | None = None

    ttl_seconds: int = 3600 * 24

    config: MessageRequestImportConfig = MessageRequestImportConfig()
