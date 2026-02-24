from typing import Annotated

from dependency_injector.wiring import Provide, inject

from src.base.ports.repositories.cache_repository import AbstractCacheRepository
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
from src.messaging.ports.messengers.capabilities.auth.errors import InvalidPasswordError


async def password_login_use_case(
    *,
    session_id: int,
    password: str,
    uow: AsyncUnitOfWork,
    user: BaseUser,
    registry: MessengerRegistry,
    cache_repo: AbstractCacheRepository,
) -> SessionDTO:
    session = await uow.session_repo.get_by_id(id=session_id)
    if session is None:
        raise NotFoundException(entity=Session)

    if session.user_id != user.id:
        raise ForbiddenException("You do not own this session")

    if not session.session_str:
        raise BadRequestException("Session is missing auth data")

    # Get messenger from session (should support Password2FAPort)
    messenger = await registry.for_session(session)
    if not isinstance(messenger, Password2FAPort):
        raise BadRequestException(
            "Messenger does not support 2FA password authentication"
        )
    try:
        new_session_str = await messenger.two_factor_authenticate(password)
    except InvalidPasswordError:
        raise BadRequestException("Invalid password.")

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
