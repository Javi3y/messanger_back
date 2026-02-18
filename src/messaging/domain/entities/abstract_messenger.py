from abc import abstractmethod

from src.files.domain.entities.file import File
from src.messaging.domain.entities.contact import Contact
from src.messaging.domain.entities.session import Session


class AbstractMessenger:
    session: Session | None = None

    @abstractmethod
    async def send_message(
        self,
        contact: Contact,
        text: str,
        file: File | None = None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def send_media(
        self,
        contact: Contact,
        text: str | None,
        file: File,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def set_session(self, session: Session | None) -> None:
        raise NotImplementedError()
