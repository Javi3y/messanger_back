from datetime import datetime

from src.base.domain.dto import BaseDTO


class FileDTO(BaseDTO):
    def __init__(
        self,
        id: int,
        uri: str,
        name: str,
        size: int | None = None,
        content_type: str | None = None,
        etag: str | None = None,
        created_at: datetime | None = None,
        modified_at: datetime | None = None,
        meta: dict[str, str] | None = None,
        download_url: str | None = None,
    ):
        self.id = id
        self.uri = uri
        self.name = name
        self.size = size
        self.content_type = content_type
        self.etag = etag
        self.created_at = created_at
        self.modified_at = modified_at
        self.meta = meta or {}
        self.download_url = download_url
