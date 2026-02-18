from dataclasses import dataclass
from typing import Type

from src.messaging.domain.enums.messenger_type import MessengerType
from src.messaging.ports.messengers.base import AbstractMessenger
from src.messaging.ports.messengers.capabilities.auth.otp import OtpAuthPort
from src.messaging.ports.messengers.capabilities.auth.password_2fa import (
    Password2FAPort,
)
from src.messaging.ports.messengers.capabilities.auth.qr import QrAuthPort
from src.messaging.ports.messengers.capabilities.contact.phone_number import (
    PhoneNumberContactPort,
)
from src.messaging.ports.messengers.capabilities.contact.username import (
    UsernameContactPort,
)
from src.messaging.ports.messengers.capabilities.contact.user_id import (
    UserIdContactPort,
)
from src.messaging.ports.messengers.capabilities.polls import PollsPort


@dataclass(frozen=True, slots=True)
class MessengerDescriptor:
    type: MessengerType
    display_name: str
    features: set[str]
    auth_methods: set[str]
    contact_identifiers: set[str]


def describe_messenger_cls(
    messenger_type: MessengerType,
    messenger_cls: Type[AbstractMessenger],
    display_name: str | None = None,
) -> MessengerDescriptor:
    name = (
        display_name
        or getattr(messenger_cls, "display_name", None)
        or messenger_type.value.title()
    )

    features: set[str] = {"send_text", "send_media"}
    auth: set[str] = set()
    contact: set[str] = set()

    if issubclass(messenger_cls, PollsPort):
        features.add("polls")

    if issubclass(messenger_cls, OtpAuthPort):
        auth.add("otp")
    if issubclass(messenger_cls, Password2FAPort):
        auth.add("2fa_password")
    if issubclass(messenger_cls, QrAuthPort):
        auth.add("qr")

    if issubclass(messenger_cls, PhoneNumberContactPort):
        contact.add("phone_number")
    if issubclass(messenger_cls, UsernameContactPort):
        contact.add("username")
    if issubclass(messenger_cls, UserIdContactPort):
        contact.add("user_id")

    return MessengerDescriptor(
        type=messenger_type,
        display_name=name,
        features=features,
        auth_methods=auth,
        contact_identifiers=contact,
    )


def describe_messenger(
    messenger_type: MessengerType,
    messenger: AbstractMessenger,
    display_name: str | None = None,
) -> MessengerDescriptor:
    cls = type(messenger)
    name = (
        display_name
        or getattr(cls, "display_name", None)
        or messenger_type.value.title()
    )

    features: set[str] = {"send_text", "send_media"}
    auth: set[str] = set()
    contact: set[str] = set()

    if isinstance(messenger, PollsPort):
        features.add("polls")
    if isinstance(messenger, OtpAuthPort):
        auth.add("otp")
    if isinstance(messenger, Password2FAPort):
        auth.add("2fa_password")
    if isinstance(messenger, QrAuthPort):
        auth.add("qr")
    if isinstance(messenger, PhoneNumberContactPort):
        contact.add("phone_number")
    if isinstance(messenger, UsernameContactPort):
        contact.add("username")
    if isinstance(messenger, UserIdContactPort):
        contact.add("user_id")

    return MessengerDescriptor(
        type=messenger_type,
        display_name=name,
        features=features,
        auth_methods=auth,
        contact_identifiers=contact,
    )
