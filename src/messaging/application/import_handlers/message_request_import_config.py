from typing import ClassVar

from pydantic import Field

from src.importing.domain.dtos.base_import_config import BaseImportConfig
from src.importing.domain.enums.unknown_columns_policy import UnknownColumnsPolicy


class MessageRequestImportConfig(BaseImportConfig):
    import_type: ClassVar[str] = "message_request"

    # optional: turn on generic constraints from the base
    allowed_required_keys: ClassVar[set[str] | None] = {"phone_number"}
    required_must_include: ClassVar[set[str]] = frozenset({"phone_number"})
    allowed_optional_keys: ClassVar[set[str] | None] = {
        "username",
        "user_id",
        "text",
        "sending_time",
    }

    required: dict[str, str] = Field(
        default_factory=lambda: {"phone_number": "phone_number"}
    )
    optional: dict[str, str] = Field(
        default_factory=lambda: {
            "username": "username",
            "user_id": "user_id",
            "text": "text",
            "sending_time": "sending_time",
        }
    )

    extras: dict[str, str] = Field(default_factory=dict)

    unknown_columns_policy: UnknownColumnsPolicy = UnknownColumnsPolicy.error
    stop_on_row_error: bool = False
    max_errors: int = 500
