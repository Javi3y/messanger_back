from abc import ABC, abstractmethod

from src.files.domain.dtos.file_dto import FileDTO


class FileQueriesPort(ABC):
    @abstractmethod
    async def get_file_with_owner(self, *, file_id: int) -> FileDTO | None:
        raise NotImplementedError

    @abstractmethod
    async def list_files_with_owner(
        self,
        *,
        user_id: int,
        include_public: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FileDTO]:
        raise NotImplementedError
