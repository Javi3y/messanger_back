from datetime import datetime

from app.schemas.base import AbstractBaseModel
from app.v1.users.schemas.v1_responses import V1BaseUserResponse


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
    user: V1BaseUserResponse | None = None
    is_public: bool
    download_url: str
