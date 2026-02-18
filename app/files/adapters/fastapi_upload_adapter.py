from fastapi import UploadFile

from src.files.ports.services.upload_port import UploadedFilePort

class FastAPIUploadedFile(UploadedFilePort):

    def __init__(self, upload_file: UploadFile) -> None:
        self._upload_file = upload_file

    async def read(self) -> bytes:
        return await self._upload_file.read()

    def filename(self) -> str:
        return self._upload_file.filename or ""

    def content_type(self) -> str | None:
        return self._upload_file.content_type
