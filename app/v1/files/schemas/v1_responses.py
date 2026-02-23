from datetime import datetime
from typing import Any

from pydantic import field_validator

from app.schemas.base import AbstractBaseModel
from src.base.domain.dto import BaseDTO


class V1FileResponse(AbstractBaseModel):
    id: int
    uri: str | None = None
    name: str | None = None
    size: int | None = None
    content_type: str | None = None
    etag: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    meta: dict[str, str] | None = None
    user: Any | None = None
    is_public: bool
    download_url: str

    @field_validator("user", mode="before")
    @classmethod
    def convert_dto_user(cls, v):
        if isinstance(v, BaseDTO):
            return v.dump(exclude_none=True)
        return v
