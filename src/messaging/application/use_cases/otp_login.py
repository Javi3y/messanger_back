from typing import Annotated

from dependency_injector.wiring import Provide, inject

from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.messaging.ports.messengers.capabilities.auth.otp import OtpAuthPort
from src.messaging.ports.messengers.capabilities.auth.password_2fa import (
    Password2FAPort,
)
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.messaging.domain.dtos.session_dto import SessionDTO
from src.messaging.domain.entities.session import Session
from src.users.domain.entities.base_user import BaseUser
from src.base.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)


async def otp_login_use_case(
    *,
    session_id: int,
    otp: int,
    uow: AsyncUnitOfWork,
    user: BaseUser,
    registry: MessengerRegistry,
    cache_repo: AbstractCacheRepository,
) -> SessionDTO:
    # Get session
    session = await uow.session_repo.get_by_id(id=session_id)
    if session is None:
        raise NotFoundException(entity=Session)

    if session.user_id != user.id:
        raise ForbiddenException("You do not own this session")

    # Get cached OTP context and validate
    cache_key = f"{session.session_type.value}-session-{session.id}"
    cached_data = await cache_repo.get(key=cache_key)
    if cached_data is None:
        raise BadRequestException("OTP session expired or not found")

    session_str, otp_context = cached_data

    # Get messenger and validate OTP
    messenger = await registry.for_session(session)

    if isinstance(messenger, OtpAuthPort):
        # Attach session and validate OTP
        try:
            new_session_str = await messenger.validate_otp(
                otp=otp,
                phone=session.phone_number,
                otp_context=otp_context,
            )
        except Exception as e:
            raise BadRequestException(f"Invalid OTP: {str(e)}")

    # Clear OTP context from cache
    await cache_repo.delete(key=cache_key)

    session.session_str = new_session_str
    session.is_active = messenger.is_valid

    updated_session = await uow.session_repo.update(entity=session)
    if updated_session.id is None:
        raise BadRequestException("Session id is required")

    session_dto = await uow.messaging_queries.get_session_details(
        session_id=int(updated_session.id)
    )
    if session_dto is None:
        raise NotFoundException(entity=Session)

    return session_dto
