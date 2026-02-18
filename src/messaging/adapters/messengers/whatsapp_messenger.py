"""
WhatsApp Messenger Adapter.

This adapter implements WhatsApp-specific business logic using the WhatsappServicePort
to interact with WhatsApp via Evolution API.
"""

import base64
import inspect
import mimetypes
import uuid

from src.files.domain.entities.file import File
from src.files.ports.services.file_service import FileServicePort
from src.messaging.domain.entities.contact import Contact
from src.messaging.domain.entities.session import Session
from src.messaging.domain.enums.messenger_type import MessengerType
from src.messaging.ports.messengers.base import AbstractMessenger
from src.messaging.ports.messengers.capabilities.auth.qr import QrAuthPort
from src.messaging.ports.messengers.capabilities.contact.phone_number import (
    PhoneNumberContactPort,
)
from src.messaging.ports.services.whatsapp_service import WhatsappServicePort


class WhatsappMessenger(AbstractMessenger, QrAuthPort, PhoneNumberContactPort):
    session: Session | None = None

    def __init__(
        self,
        service: WhatsappServicePort,
        file_service: FileServicePort,
    ):
        super().__init__(file_service)
        self.service = service

    async def set_session(self, session: Session | None) -> None:
        if session and getattr(session, "session_type", None) != MessengerType.whatsapp:
            raise ValueError(
                "Session.session_type must be MessengerType.whatsapp for WhatsappMessenger"
            )
        self.session = session

    def _generate_instance_name(self, title: str, session_uuid: uuid.UUID) -> str:
        # Keep this stable (changing it will break existing instances in Evolution)
        return f"{title}-{str(session_uuid)}"

    # --------------------------------------------------------------------- #
    # QR Auth flow (QrAuthPort)
    # --------------------------------------------------------------------- #

    async def login(
        self,
        integration: str = "WHATSAPP-BAILEYS",
    ) -> str:
        if not self.session:
            raise Exception("Session is not set. Please set a session first.")

        session_uuid = self.session.uuid if self.session.uuid else uuid.uuid4()
        instance_name = self._generate_instance_name(self.session.title, session_uuid)

        await self.service.create_instance(instance_name=instance_name)
        res = await self.service.connect_instance(instance_name=instance_name)

        self.session.uuid = session_uuid
        return res["code"]

    # --------------------------------------------------------------------- #
    # Messaging (AbstractMessenger)
    # --------------------------------------------------------------------- #

    async def send_text(self, contact: Contact, text: str) -> None:
        if not self.session:
            raise Exception("No active session. Please log in first.")
        if not self.session.uuid:
            raise Exception("Session.uuid is missing. Please log in first.")

        await self.service.send_text(
            instance_name=self._generate_instance_name(
                self.session.title, self.session.uuid
            ),
            number=contact.phone_number,
            text=text,
        )

    def _file_to_whatsapp_mimetype(self, f: File) -> str:
        if getattr(f, "content_type", None):
            return f.content_type

        guessed, _ = mimetypes.guess_type(
            getattr(f, "name", "") or getattr(f, "uri", "") or ""
        )
        return guessed or "application/octet-stream"

    def _mimetype_to_evolution_mediatype(self, mimetype: str) -> str:
        # Evolution sendMedia typically expects one of: image | video | document
        if mimetype.startswith("image/"):
            return "image"
        if mimetype.startswith("video/"):
            return "video"
        return "document"

    async def _file_to_whatsapp_media(self, f: File) -> str:
        # If you later decide to store precomputed base64 somewhere (e.g., f.base64), this picks it up.
        b64 = getattr(f, "base64", None)
        if b64:
            return b64

        content: bytes = await self.file_service.read(f.uri)
        return base64.b64encode(content).decode("ascii")

    def _supports_kw(self, fn, name: str) -> bool:
        try:
            return name in inspect.signature(fn).parameters
        except (TypeError, ValueError):
            return False

    async def send_media(self, contact: Contact, text: str | None, file: File) -> None:
        if not self.session:
            raise Exception("No active session. Please log in first.")
        if not self.session.uuid:
            raise Exception("Session.uuid is missing. Please log in first.")

        instance_name = self._generate_instance_name(
            self.session.title, self.session.uuid
        )

        mimetype = self._file_to_whatsapp_mimetype(file)
        media_value = await self._file_to_whatsapp_media(file)

        # Some Evolution versions accept an 'options' object; if supported, encoding=True indicates base64.
        options: dict[str, object] = {"encoding": True}

        kwargs: dict[str, object] = {
            "instance_name": instance_name,
            "number": contact.phone_number,
            "media": media_value,
            "mimetype": mimetype,
            "caption": text,
        }

        # If your WhatsappService/HttpService supports these Evolution v2 fields, pass them.
        if self._supports_kw(self.service.send_media, "mediatype"):
            kwargs["mediatype"] = self._mimetype_to_evolution_mediatype(mimetype)

        # Some clients use snake_case, others camelCase.
        if self._supports_kw(self.service.send_media, "file_name"):
            kwargs["file_name"] = file.name
        elif self._supports_kw(self.service.send_media, "fileName"):
            kwargs["fileName"] = file.name

        if self._supports_kw(self.service.send_media, "options"):
            kwargs["options"] = options

        await self.service.send_media(**kwargs)

    async def send_message(
        self, contact: Contact, text: str, file: File | None = None
    ) -> None:
        if file:
            return await self.send_media(contact=contact, text=text, file=file)

        return await self.send_text(contact=contact, text=text)
