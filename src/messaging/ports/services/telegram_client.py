from abc import ABC, abstractmethod
from typing import Optional


class TelegramClientPort(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_connected(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def is_authorized(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_code_request(self, phone: str) -> object:
        raise NotImplementedError

    @abstractmethod
    async def sign_in(self, phone: str, code: str, phone_code_hash: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def sign_in_with_password(self, password: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_session_string(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def set_session_string(self, session_string: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, target: str, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_file(self, target: str, file, caption: Optional[str] = None) -> None:
        raise NotImplementedError
