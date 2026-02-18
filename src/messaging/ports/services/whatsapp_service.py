from abc import abstractmethod
from typing import Literal

from src.base.ports.services.client import AbstractClient
from src.base.ports.services.service import AsyncAbstractService


class WhatsappServicePort(AsyncAbstractService):
    def __init__(self, client: AbstractClient):
        super().__init__(client)

    @abstractmethod
    async def create_instance(
        self,
        instance_name: str,
        qrcode: bool | None = True,
        integration: Literal[
            "WHATSAPP-BAILEYS", "WHATSAPP-BUSINESS", "EVOLUTION"
        ] = "WHATSAPP-BAILEYS",
    ):
        raise NotImplementedError

    @abstractmethod
    async def connect_instance(
        self,
        instance_name: str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def connection_status(
        self,
        instance_name: str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def send_text(
        self,
        instance_name: str,
        number: str,
        text: str,
    ):
        raise NotImplementedError

    @abstractmethod
    async def send_media(
        self,
        instance_name: str,
        number: str,
        media: str,
        mimetype: str,
        caption: str | None = None,
    ):
        raise NotImplementedError
