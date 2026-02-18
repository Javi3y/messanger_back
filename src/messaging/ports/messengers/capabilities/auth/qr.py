from abc import ABC, abstractmethod


class QrAuthPort(ABC):

    @abstractmethod
    async def login(self, *, integration: str = "WHATSAPP-BAILEYS") -> str:
        raise NotImplementedError
