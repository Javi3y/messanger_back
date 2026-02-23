from typing import cast

from src.base.exceptions import BadRequestException
from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.messaging.domain.dtos.start_otp_session_dto import StartOtpSessionDTO
from src.messaging.domain.entities.session import Session
from src.messaging.domain.enums.messenger_type import MessengerType
from src.messaging.ports.messengers.capabilities.auth.otp import OtpAuthPort
from src.users.domain.entities.base_user import BaseUser


async def start_otp_session_use_case(
    *,
    title: str,
    phone_number: str,
    messenger_type: MessengerType,
    uow: AsyncUnitOfWork,
    user: BaseUser,
    registry: MessengerRegistry,
    cache_repo: AbstractCacheRepository,
) -> StartOtpSessionDTO:
    user_id = user.id
    if user_id is None:
        raise BadRequestException(detail="User id is required")
    user_id = cast(int, user_id)

    messenger = registry.get_messenger(messenger_type)
    if not isinstance(messenger, OtpAuthPort):
        raise BadRequestException(
            detail=f"Messenger {messenger_type.value} does not support OTP login"
        )

    await messenger.set_session(None)
    session_str, otp_context = await messenger.login(phone_number)

    session = Session(
        user_id=user_id,
        title=title,
        session_type=messenger_type,
        session_str=session_str,
        phone_number=phone_number,
        is_active=False,
    )
    session = await uow.session_repo.add(entity=session)
    await uow.flush()

    if session.id is None:
        raise BadRequestException(detail="Session id is required")

    await cache_repo.set(
        key=f"{messenger_type.value}-session-{session.id}",
        value=(session_str, otp_context),
        ttl=600,
    )

    return StartOtpSessionDTO(
        session_id=session.id,
        message="Use /sessions/verify/opt to complete authentication",
    )
