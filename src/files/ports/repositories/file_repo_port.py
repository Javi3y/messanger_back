from abc import ABC, abstractmethod
from src.base.ports.repositories.repository import AbstractRepository
from src.files.domain.entities.file import File


class FileRepositoryPort(AbstractRepository, ABC):

    @abstractmethod
    async def add(
        self,
        *,
        entity: File,
        **kwargs,
    ) -> File:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        *,
        entity: File,
        **kwargs,
    ) -> File:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        *,
        id: int,
        soft_delete: bool = True,
        **kwargs,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[File]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        **kwargs,
    ) -> File | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_uri(
        self,
        *,
        uri: str,
        include_deleted: bool = False,
        **kwargs,
    ) -> File | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_etag(
        self,
        *,
        etag: str,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[File]:
        raise NotImplementedError

    @abstractmethod
    async def search_by_name(
        self,
        *,
        name_like: str,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[File]:
        raise NotImplementedError
