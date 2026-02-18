from abc import ABC, abstractmethod


class Password2FAPort(ABC):

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def two_factor_authenticate(self, two_factor_password: str) -> str:
        raise NotImplementedError
