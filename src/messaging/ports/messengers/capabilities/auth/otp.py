from abc import ABC, abstractmethod


class OtpAuthPort(ABC):
    @property
    @abstractmethod
    def is_valid(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def login(self, phone_number: str) -> tuple[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def validate_otp(self, otp: int | str, phone: str, otp_context: str) -> str:
        raise NotImplementedError
