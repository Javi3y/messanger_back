"""Messaging response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from src.base.domain.dto import BaseDTO


class V1MessengerDescriptorResponse(BaseModel):
    """Response model for messenger descriptor."""

    type: str
    display_name: str
    features: set[str]
    auth_methods: set[str]
    contact_identifiers: set[str]


class V1SessionResponse(BaseModel):
    """Session entity response."""

    id: int
    title: str
    phone_number: str | None = None
    session_type: str
    is_active: bool
    user_id: int


class V1QrCodeResponse(BaseModel):
    """QR code response."""

    qr_code: str


class V1MessageRequestResponse(BaseModel):
    """
    Message request response with nested user and files.

    Automatically converts BaseDTO instances to dicts using dump().
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    user: Any
    session_id: int
    csv_file: Any | None = None
    attachment_file: Any | None = None
    title: str | None = None
    default_text: str | None = None
    sending_time: datetime | None = None

    @field_validator("user", "csv_file", "attachment_file", mode="before")
    @classmethod
    def convert_dtos(cls, v):
        """Convert BaseDTO instances to dict using dump()."""
        if isinstance(v, BaseDTO):
            return v.dump(exclude_none=True)
        return v
