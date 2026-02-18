from abc import ABC, abstractmethod


class UploadedFilePort(ABC):
    @abstractmethod
    async def read(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def filename(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def content_type(self) -> str | None:
        raise NotImplementedError
