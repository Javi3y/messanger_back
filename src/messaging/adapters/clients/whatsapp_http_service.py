from typing import Literal
from src.base.ports.services.abstract_http_client import AbstractAsyncHttpClient
from src.base.ports.services.abstract_http_service import AbstractAsyncHttpService
from src.messaging.ports.services.whatsapp_service import WhatsappServicePort


class WhatsappHttpService(AbstractAsyncHttpService, WhatsappServicePort):
    _token = ""

    def __init__(
        self,
        client: AbstractAsyncHttpClient,
        key: str,
    ):
        super().__init__(client)
        self.key = key

    async def authenticate(self, **kwargs):
        self._token = self.key

    async def get_headers(self):
        if not self._token:
            await self.authenticate()
        return {"apikey": self._token}

    async def create_instance(
        self,
        instance_name: str,
        qrcode: bool | None = True,
        integration: Literal[
            "WHATSAPP-BAILEYS", "WHATSAPP-BUSINESS", "EVOLUTION"
        ] = "WHATSAPP-BAILEYS",
    ):
        payload = {
            "instanceName": instance_name,
            "integration": integration,
            **({"qrcode": qrcode} if qrcode is not None else {}),
        }
        response = await self.client.request(
            method="POST",
            path="/instance/create",
            json_data=payload,
            headers=await self.get_headers(),
        )
        return response

    async def connect_instance(
        self,
        instance_name: str,
    ):

        response = await self.client.request(
            method="GET",
            path=f"/instance/connect/{instance_name}",
            headers=await self.get_headers(),
        )
        return response

    async def connection_status(
        self,
        instance_name: str,
    ):

        response = await self.client.request(
            method="GET",
            path=f"/instance/connectionState/{instance_name}",
            headers=await self.get_headers(),
        )
        return response

    async def send_text(
        self,
        instance_name: str,
        number: str,
        text: str,
    ):
        payload = {
            "number": number,
            "text": text,
        }
        response = await self.client.request(
            method="POST",
            path=f"/message/sendText/{instance_name}",
            json_data=payload,
            headers=await self.get_headers(),
        )
        return response

    async def send_media(
        self,
        *,
        instance_name: str,
        number: str,
        mediatype: str,
        mimetype: str,
        caption: str,
        media: str,
        file_name: str,
        delay: int | None = None,
    ):
        payload = {
            "number": number,
            "mediatype": mediatype,
            "mimetype": mimetype,
            "caption": caption,
            "media": media,
            "fileName": file_name,
        }
        if delay is not None:
            payload = {**payload, "delay": delay}

        response = await self.client.request(
            method="POST",
            path=f"/message/sendMedia/{instance_name}",
            headers=await self.get_headers(),
            json_data=payload,
        )

        return response
