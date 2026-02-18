from datetime import datetime
from app.schemas.base import AbstractBaseModel


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
    download_url: str
