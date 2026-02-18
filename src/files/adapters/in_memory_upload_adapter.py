from src.files.ports.services.upload_port import UploadedFilePort


class InMemoryUploadedFile(UploadedFilePort):
    def __init__(self, *, filename: str, content: bytes, content_type: str):
        self._filename = filename
        self._content = content
        self._content_type = content_type

    async def read(self) -> bytes:
        return self._content

    def filename(self) -> str:
        return self._filename

    def content_type(self) -> str:
        return self._content_type
