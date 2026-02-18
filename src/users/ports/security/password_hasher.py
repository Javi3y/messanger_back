from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    @abstractmethod
    def is_hashed(self, value: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def ensure_hashed(self, password: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def hash(self, password: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        raise NotImplementedError
