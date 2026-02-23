from datetime import datetime
from typing import TYPE_CHECKING

from src.base.domain.dto import BaseDTO
from src.users.domain.dtos.user_dto import UserDTO

if TYPE_CHECKING:
    from src.files.domain.entities.file import File
    from src.users.domain.entities.base_user import BaseUser


class FileDTO(BaseDTO):
    __serialize_exclude__ = {"owner_id"}

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
        owner_id: int | None = None,
        user: UserDTO | None = None,
        is_public: bool = True,
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
        self.owner_id = owner_id
        self.user = user
        self.is_public = is_public
        self.download_url = download_url

    @classmethod
    def from_file(
        cls,
        *,
        file: "File",
        user: "BaseUser | None" = None,
        download_url: str | None = None,
    ) -> "FileDTO":
        user_dto = None
        if user is not None and user.id is not None:
            user_dto = UserDTO(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                sur_name=user.sur_name,
                phone_number=user.phone_number,
                user_type=user.user_type,
            )

        return cls(
            id=file.id if file.id is not None else 0,
            uri=file.uri,
            name=file.name,
            size=file.size,
            content_type=file.content_type,
            etag=file.etag,
            created_at=file.created_at,
            modified_at=file.modified_at,
            meta=file.meta,
            owner_id=file.user_id,
            user=user_dto,
            is_public=file.user_id is None,
            download_url=download_url or file.download_url,
        )
