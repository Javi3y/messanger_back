from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Mapping


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FileInfo:

    uri: str  # e.g. "s3://bucket/key", "file:///var/data/x.bin", "ntfs://share/path"
    size: int | None = None  # bytes, if known
    content_type: str | None = None  # e.g. "image/png"
    etag: str | None = None  # strong/weak validator, if the backend supports it
    modified_at: datetime | None = None  # last-modified in UTC


class FileServicePort(ABC):
    @abstractmethod
    async def read(self, uri: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self, uri: str, chunk_size: int = 1024 * 1024
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError

    @abstractmethod
    def build_uri(self, *, prefix: str, name: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def build_download_url(self, *, uri: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def write(
        self,
        uri: str,
        data: bytes,
        *,
        content_type: str | None = None,
        meta: Mapping[str, str] | None = None,
        overwrite: bool = True,
    ) -> FileInfo:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, uri: str, *, missing_ok: bool = True) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, uri: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def stat(self, uri: str) -> FileInfo:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self, prefix: str, *, recursive: bool = False
    ) -> AsyncIterator[FileInfo]:
        raise NotImplementedError
