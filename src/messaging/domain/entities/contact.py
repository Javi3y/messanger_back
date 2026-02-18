from src.messaging.domain.enums.messenger_type import MessengerType


class Contact:
    contact_type: MessengerType
    id: str | None = None
    username: str | None = None
    phone_number: str

    def __init__(
        self,
        contact_type: MessengerType,
        id: str | None = None,
        username: str | None = None,
        phone_number: str | None = None,
    ) -> None:
        self.contact_type = contact_type
        self.username = username
        self.id = id
        self.phone_number = phone_number
        if contact_type == MessengerType.whatsapp:
            if id or username or not phone_number:
                raise ValueError("WhatsApp contact must only have a phone number")
        elif contact_type == MessengerType.telegram:
            if not (id or username or phone_number):
                raise ValueError(
                    "Telegram contact must have at least one of id, username, or phone_number"
                )
