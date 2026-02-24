from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from app.deps.providers import get_uow
from app.v1.messaging.schemas import v1_requests as rqm
from app.v1.messaging.schemas import v1_responses as rsm
from app.v1.messaging.schemas.v1_responses import (
    V1CreateMessageRequestImportResponse,
    V1MessageRequestResponse,
    V1SendMessageResponse,
)
from app.v1.users.deps.get_current_user import get_current_user
from app.container import ApplicationContainer
from src.base.exceptions import BadRequestException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.messaging.application.use_cases.send_message import send_message_use_case
from src.messaging.application.use_cases.get_message_request import (
    get_message_request_use_case,
)
from src.messaging.application.use_cases.create_message_request_import import (
    create_message_request_import_use_case,
)
from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)
from src.users.domain.entities.base_user import BaseUser

router = APIRouter(prefix="", tags=["messages"])


@router.post("/message", response_model=V1SendMessageResponse)
async def message(
    request: rqm.V1MessageRequest,
    user: BaseUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> V1SendMessageResponse:
    if user.id is None:
        raise BadRequestException(detail="User id is required")

    async with uow:
        dto = await send_message_use_case(
            session_id=request.session_id,
            phone_number=request.contact.phone_number,
            username=request.contact.username,
            user_id=request.contact.id,
            text=request.text,
            file_id=request.file_id,
            current_user=user,
            uow=uow,
        )
        await uow.commit()

        return rsm.V1SendMessageResponse(**dto.dump())


@router.get("/message-requests/{message_request_id}")
async def get_message_request(
    message_request_id: int,
    user: BaseUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> V1MessageRequestResponse:
    async with uow:
        dto = await get_message_request_use_case(
            message_request_id=message_request_id,
            user=user,
            uow=uow,
        )

        return rsm.V1MessageRequestResponse(**dto.dump())


@router.post(
    "/message-requests/import", response_model=V1CreateMessageRequestImportResponse
)
@inject
async def create_message_request_import(
    request: rqm.V1ImportMessageRequest,
    user: BaseUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
    import_staging_repo: ImportStagingRepositoryPort = Depends(
        Provide[ApplicationContainer.import_staging_repo]
    ),
) -> V1CreateMessageRequestImportResponse:

    async with uow:
        dto = await create_message_request_import_use_case(
            uow=uow,
            user=user,
            session_id=request.session_id,
            file_id=request.file_id,
            title=request.title,
            default_text=request.default_text,
            default_sending_time=request.default_sending_time,
            attachment_file_id=request.attachment_file_id,
            import_config=request.config.model_dump(),
            ttl_seconds=request.ttl_seconds,
            import_staging_repo=import_staging_repo,
        )
        await uow.commit()
        return V1CreateMessageRequestImportResponse(**dto.dump())
