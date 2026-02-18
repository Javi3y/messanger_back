from src.base.exceptions import BadRequestException
from src.messaging.domain.enums.messenger_type import MessengerType


def validate_contact_for_messenger(
    *,
    phone_number: str | None,
    username: str | None,
    user_id: str | None,
    messenger_type: MessengerType,
) -> None:
    if messenger_type == MessengerType.whatsapp:
        if user_id or username or not phone_number:
            raise BadRequestException(
                "WhatsApp contact must have only a phone number (no id or username)"
            )
    elif messenger_type == MessengerType.telegram:
        if not (user_id or username or phone_number):
            raise BadRequestException(
                "Telegram contact must have at least one of: id, username, or phone number"
            )
