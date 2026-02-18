from abc import ABC, abstractmethod
from typing import Optional

from src.files.domain.entities.file import File
from src.files.ports.services.file_service import FileServicePort
from src.messaging.domain.entities.contact import Contact
from src.messaging.domain.entities.session import Session


class AbstractMessenger(ABC):

    session: Optional[Session] = None

    def __init__(
        self,
        file_service: FileServicePort,
    ):
        self.file_service = file_service
        self.session: Optional[Session] = None

    @abstractmethod
    async def set_session(self, session: Session | None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_message(
        self, contact: Contact, text: str, file: File | None = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_text(self, contact: Contact, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_media(self, contact: Contact, text: str | None, file: File) -> None:
        raise NotImplementedError
