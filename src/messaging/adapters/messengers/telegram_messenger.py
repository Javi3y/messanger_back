import base64
import io
import mimetypes

from src.files.domain.entities.file import File
from src.files.ports.services.file_service import FileServicePort
from src.messaging.domain.entities.contact import Contact
from src.messaging.domain.entities.session import Session
from src.messaging.domain.enums.messenger_type import MessengerType
from src.messaging.ports.messengers.base import AbstractMessenger
from src.messaging.ports.messengers.capabilities.auth.otp import OtpAuthPort
from src.messaging.ports.messengers.capabilities.auth.password_2fa import (
    Password2FAPort,
)
from src.messaging.ports.messengers.capabilities.auth.errors import (
    ExpiredCodeError,
    InvalidCodeError,
    InvalidPasswordError,
    SessionPasswordNeededError,
)
from src.messaging.ports.messengers.capabilities.contact.phone_number import (
    PhoneNumberContactPort,
)
from src.messaging.ports.messengers.capabilities.contact.username import (
    UsernameContactPort,
)
from src.messaging.ports.messengers.capabilities.contact.user_id import (
    UserIdContactPort,
)
from src.messaging.ports.services.telegram_client import (
    TelegramClientPort,
)


class TelegramMessenger(
    AbstractMessenger,
    OtpAuthPort,
    Password2FAPort,
    PhoneNumberContactPort,
    UsernameContactPort,
    UserIdContactPort,
):
    is_valid: bool = False

    def __init__(
        self,
        client: TelegramClientPort,
        file_service: FileServicePort,
    ):
        super().__init__(file_service)
        self.client = client

    async def set_session(self, session: Session | None) -> None:
        if session and getattr(session, "session_type", None) != MessengerType.telegram:
            raise ValueError(
                "Session.session_type must be MessengerType.telegram for TelegramMessenger"
            )

        self.session = session

        if session and getattr(session, "session_str", None):
            self.client.set_session_string(session.session_str)
        else:
            self.client.set_session_string("")

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _persist_session(self) -> str:
        session_str = self.client.get_session_string()

        if self.session is not None:
            self.session.session_str = session_str

        return session_str

    def _resolve_target(self, contact: Contact) -> str:
        if getattr(contact, "id", None):
            return contact.id
        if getattr(contact, "username", None):
            return contact.username
        if getattr(contact, "phone_number", None):
            return contact.phone_number
        raise ValueError(
            "Telegram contact must have at least id, username, or phone_number."
        )

    def _telegram_filename(self, f: File) -> str:
        name = (getattr(f, "name", None) or "").strip()
        if name:
            return name

        # Fallback: derive from content_type
        ct = (getattr(f, "content_type", None) or "").split(";", 1)[0].strip()
        ext = mimetypes.guess_extension(ct) or ".bin"

        return f"file{ext}"

    async def _file_to_bytes(self, f: File) -> bytes:
        """Convert a file entity to bytes for sending."""
        # Check if file has pre-computed base64
        b64 = getattr(f, "base64", None)
        if b64:
            # Strip data URL prefix if present
            if b64.startswith("data:") and "," in b64:
                b64 = b64.split(",", 1)[1]
            return base64.b64decode(b64)

        # Otherwise read from storage
        return await self.file_service.read(f.uri)

    # --------------------------------------------------------------------- #
    # Auth flow (OtpAuthPort)
    # --------------------------------------------------------------------- #

    @property
    def is_valid(self) -> bool:
        return object.__getattribute__(self, "_is_valid")

    @is_valid.setter
    def is_valid(self, value: bool) -> None:
        object.__setattr__(self, "_is_valid", value)

    async def login(self, phone_number: str) -> tuple[str, str]:
        result = await self.client.send_code_request(phone_number)
        session_str = self._persist_session()
        phone_code_hash = result.phone_code_hash
        await self.client.disconnect()

        return session_str, phone_code_hash

    async def validate_otp(
        self,
        otp: int | str,
        phone: str,
        otp_context: str,
    ) -> str:
        try:
            await self.client.sign_in(
                phone=phone,
                code=str(int(otp)),
                phone_code_hash=otp_context,
            )

        except SessionPasswordNeededError:
            # 2FA enabled on account; need password
            self._is_valid = False
            await self.client.disconnect()
            return self._persist_session()

        except (InvalidCodeError, ExpiredCodeError):
            self._is_valid = False
            # Let caller handle this (e.g. show error to user)
            await self.client.disconnect()
            raise

        # Logged in successfully without 2FA
        self._is_valid = True
        await self.client.disconnect()
        return self._persist_session()

    # --------------------------------------------------------------------- #
    # 2FA flow (Password2FAPort)
    # --------------------------------------------------------------------- #

    async def two_factor_authenticate(self, two_factor_password: str) -> str:
        try:
            await self.client.sign_in_with_password(two_factor_password)
        except InvalidPasswordError:
            await self.client.disconnect()
            self._is_valid = False
            raise

        self._is_valid = True
        await self.client.disconnect()
        return self._persist_session()

    # --------------------------------------------------------------------- #
    # Messaging (AbstractMessenger)
    # --------------------------------------------------------------------- #

    async def send_message(self, contact: Contact, text: str, file: File | None = None):
        if file:
            return await self.send_media(contact, text, file)
        return await self.send_text(contact, text)

    async def send_text(self, contact: Contact, text: str) -> None:
        target = self._resolve_target(contact)
        await self.client.send_message(target, text)

    async def send_media(self, contact: Contact, text: str | None, file: File) -> None:
        target = self._resolve_target(contact)
        payload_bytes = await self._file_to_bytes(file)

        buf = io.BytesIO(payload_bytes)
        buf.name = self._telegram_filename(file)
        buf.seek(0)

        await self.client.send_file(target, buf, caption=text)
