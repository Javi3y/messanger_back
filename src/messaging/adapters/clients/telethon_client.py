import base64
import io
import mimetypes
from typing import Any, Optional

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError as TelethonSessionPasswordNeededError,
    PhoneCodeInvalidError as TelethonPhoneCodeInvalidError,
    PhoneCodeExpiredError as TelethonPhoneCodeExpiredError,
    PasswordHashInvalidError as TelethonPasswordHashInvalidError,
)

from src.messaging.ports.messengers.capabilities.auth.errors import (
    ExpiredCodeError,
    InvalidCodeError,
    InvalidPasswordError,
    SessionPasswordNeededError,
)
from src.messaging.ports.services.telegram_client import TelegramClientPort


def telethon_kwargs_from_proxy_url(proxy_url: str | None) -> dict[str, Any]:
    if not proxy_url:
        return {}

    from urllib.parse import urlparse, parse_qs

    def _q1(q: dict[str, list[str]], key: str) -> str | None:
        v = q.get(key)
        return v[0] if v else None

    u = urlparse(proxy_url.strip())
    host = (u.netloc or "").lower()
    path = (u.path or "").strip("/").lower()
    q = parse_qs(u.query)

    is_tme = host in {"t.me", "telegram.me", "www.t.me", "www.telegram.me"}
    is_tg = u.scheme.lower() == "tg"
    if is_tme or is_tg:
        action = (path if is_tme else (u.netloc or "")).lower()

        server = _q1(q, "server")
        port_s = _q1(q, "port")
        if not server or not port_s:
            raise ValueError("Invalid TELEGRAM_PROXY_URL: missing server/port")

        port = int(port_s)

        if action == "socks":
            user = _q1(q, "user")
            pwd = _q1(q, "pass")

            proxy: dict[str, Any] = {
                "proxy_type": "socks5",
                "addr": server,
                "port": port,
                "rdns": True,
            }
            if user:
                proxy["username"] = user
            if pwd:
                proxy["password"] = pwd
            return {"proxy": proxy}

        if action == "proxy":
            secret = _q1(q, "secret")
            if not secret:
                raise ValueError(
                    "Invalid TELEGRAM_PROXY_URL: missing secret for MTProto proxy"
                )

            from telethon import connection

            return {
                "connection": connection.ConnectionTcpMTProxyRandomizedIntermediate,
                "proxy": (server, port, secret),
            }

        raise ValueError("Invalid TELEGRAM_PROXY_URL: expected /socks or /proxy")

    scheme = u.scheme.lower()
    if scheme in {"socks5", "socks4", "http"}:
        if not u.hostname or not u.port:
            raise ValueError("Invalid TELEGRAM_PROXY_URL: missing host/port")

        proxy: dict[str, Any] = {
            "proxy_type": scheme,
            "addr": u.hostname,
            "port": int(u.port),
            "rdns": True,
        }
        if u.username:
            proxy["username"] = u.username
        if u.password:
            proxy["password"] = u.password
        return {"proxy": proxy}

    raise ValueError(f"Unsupported TELEGRAM_PROXY_URL scheme: {u.scheme}")


class TelethonClient(TelegramClientPort):
    def __init__(self, api_id: int, api_hash: str, proxy_url: Optional[str] = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self._session = StringSession()
        self.telethon_kwargs = {}
        if proxy_url:
            self.telethon_kwargs = telethon_kwargs_from_proxy_url(proxy_url)

        self.client: TelegramClient = TelegramClient(
            self._session,
            api_id,
            api_hash,
            **self.telethon_kwargs,
        )

    async def connect(self) -> None:
        if not self.client.is_connected():
            await self.client.connect()

    async def disconnect(self) -> None:
        if self.client.is_connected():
            await self.client.disconnect()

    async def is_connected(self) -> bool:
        return self.client.is_connected()

    async def is_authorized(self) -> bool:
        return await self.client.is_user_authorized()

    async def send_code_request(self, phone: str) -> object:
        await self.connect()
        return await self.client.send_code_request(phone)

    async def sign_in(self, phone: str, code: str, phone_code_hash: str) -> None:
        await self.connect()
        try:
            await self.client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=phone_code_hash,
            )
        except TelethonSessionPasswordNeededError:
            raise SessionPasswordNeededError()
        except TelethonPhoneCodeInvalidError:
            raise InvalidCodeError("Invalid OTP code")
        except TelethonPhoneCodeExpiredError:
            raise ExpiredCodeError("OTP code has expired")

    async def sign_in_with_password(self, password: str) -> None:
        await self.connect()
        try:
            await self.client.sign_in(password=password)
        except TelethonPasswordHashInvalidError:
            raise InvalidPasswordError("Invalid 2FA password")

    def get_session_string(self) -> str:
        return self.client.session.save()

    def set_session_string(self, session_string: str) -> None:
        self._session = StringSession(session_string)
        self.client = TelegramClient(
            self._session,
            self.api_id,
            self.api_hash,
            **self.telethon_kwargs,
        )

    async def send_message(self, target: str, text: str) -> None:
        await self.connect()
        try:
            await self.client.send_message(target, text)
        finally:
            await self.disconnect()

    async def send_file(self, target: str, file, caption: Optional[str] = None) -> None:
        await self.connect()
        try:
            await self.client.send_file(
                entity=target,
                file=file,
                caption=caption,
            )
        finally:
            await self.disconnect()
