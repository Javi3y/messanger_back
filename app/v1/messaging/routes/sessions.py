from fastapi import APIRouter, Depends
from src.messaging.application.use_cases.otp_login import otp_login_use_case
from src.messaging.application.use_cases.password_login import (
    password_login_use_case,
)
from src.messaging.application.use_cases.start_otp_session import (
    start_otp_session_use_case,
)
from src.messaging.application.use_cases.start_qr_session import (
    start_qr_session_use_case,
)

from app.deps.providers import get_file_service, get_uow
from app.v1.messaging.deps.providers import get_cache_repo
from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.ports.services.file_service import FileServicePort
from app.v1.messaging.schemas import v1_requests as rqm
from app.v1.messaging.schemas.v1_responses import (
    V1MessengerDescriptorResponse,
    V1SessionResponse,
)
from app.v1.users.deps.get_current_user import get_current_user
from app.v1.messaging.deps.providers import get_messenger_registry
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.users.domain.entities.base_user import BaseUser

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/messengers", response_model=list[V1MessengerDescriptorResponse])
async def list_messengers(
    registry: MessengerRegistry = Depends(get_messenger_registry),
) -> list[V1MessengerDescriptorResponse]:
    """
    List all available messengers with their capabilities.
    """
    descriptors = registry.describe_all()
    return [
        V1MessengerDescriptorResponse(
            type=d.type.value,
            display_name=d.display_name,
            features=d.features,
            auth_methods=d.auth_methods,
            contact_identifiers=d.contact_identifiers,
        )
        for d in descriptors
    ]


@router.post("/otp", response_model=dict)
async def start_otp_session(
    request: rqm.V1StartOtpSessionRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
    user: BaseUser = Depends(get_current_user),
    registry: MessengerRegistry = Depends(get_messenger_registry),
    cache_repo: AbstractCacheRepository = Depends(get_cache_repo),
) -> dict:
    async with uow:
        res = await start_otp_session_use_case(
            title=request.title,
            phone_number=request.phone_number,
            messenger_type=request.messenger_type,
            uow=uow,
            user=user,
            registry=registry,
            cache_repo=cache_repo,
        )
        await uow.commit()
        return res


@router.post("/qr", response_model=dict)
async def start_qr_session(
    request: rqm.V1StartQrSessionRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
    user: BaseUser = Depends(get_current_user),
    registry: MessengerRegistry = Depends(get_messenger_registry),
    file_service: FileServicePort = Depends(get_file_service),
) -> dict:
    async with uow:
        res = await start_qr_session_use_case(
            title=request.title,
            phone_number=request.phone_number,
            messenger_type=request.messenger_type,
            uow=uow,
            user=user,
            registry=registry,
            file_service=file_service,
        )
        await uow.commit()
        return res


@router.post("/verify/opt", response_model=V1SessionResponse)
async def verify_otp(
    request: rqm.V1TelegramOtpRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
    user: BaseUser = Depends(get_current_user),
    registry: MessengerRegistry = Depends(get_messenger_registry),
    cache_repo: AbstractCacheRepository = Depends(get_cache_repo),
) -> V1SessionResponse:
    """
    Complete OTP authentication.
    """

    async with uow:
        session = await otp_login_use_case(
            session_id=request.session_id,
            otp=request.otp,
            uow=uow,
            user=user,
            registry=registry,
            cache_repo=cache_repo,
        )
        await uow.commit()

        return V1SessionResponse(
            id=session.id,
            title=session.title,
            phone_number=session.phone_number,
            session_type=session.session_type.value,
            is_active=session.is_active,
            user_id=session.user_id,
        )


@router.post("/verify/password", response_model=V1SessionResponse)
async def verify_password(
    request: rqm.V1TelegramPasswordRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
    user: BaseUser = Depends(get_current_user),
    registry: MessengerRegistry = Depends(get_messenger_registry),
    cache_repo: AbstractCacheRepository = Depends(get_cache_repo),
) -> V1SessionResponse:
    """
    Complete 2FA password authentication.
    """

    async with uow:
        session = await password_login_use_case(
            session_id=request.session_id,
            password=request.password,
            uow=uow,
            user=user,
            registry=registry,
            cache_repo=cache_repo,
        )
        await uow.commit()

        return V1SessionResponse(
            id=session.id,
            title=session.title,
            phone_number=session.phone_number,
            session_type=session.session_type.value,
            is_active=session.is_active,
            user_id=session.user_id,
        )
