from abc import ABC, abstractmethod
from typing import Any


class JwtPort(ABC):
    @abstractmethod
    def create_access_token(
        self,
        *,
        subject: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode(self, token: str) -> dict[str, Any]:
        raise NotImplementedError
