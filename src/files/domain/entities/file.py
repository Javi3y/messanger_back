from datetime import datetime

from src.base.domain.entity import BaseEntity


class File(BaseEntity):
    repo_attr = "file_repo"
    uri: str
    name: str  # display/base name (e.g., "avatar.png")
    size: int | None = None  # bytes
    content_type: str | None = None
    etag: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    meta: dict[str, str] | None = None
    user_id: int | None = None

    download_url: str | None = None

    def __init__(
        self,
        uri: str,
        name: str,
        *,
        size: int | None = None,
        content_type: str | None = None,
        etag: str | None = None,
        created_at: datetime | None = None,
        modified_at: datetime | None = None,
        meta: dict[str, str] | None = None,
        user_id: int | None = None,
        download_url: str | None = None,
        id: int | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id, deleted_at=deleted_at)
        self.uri = uri
        self.name = name
        self.size = size
        self.content_type = content_type
        self.etag = etag
        self.created_at = created_at
        self.modified_at = modified_at
        self.meta = meta
        self.user_id = user_id
        self.download_url = download_url
