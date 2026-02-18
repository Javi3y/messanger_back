from datetime import datetime

from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from app.deps.providers import get_uow, get_file_service
from app.v1.messaging.schemas import v1_requests as rqm
from app.v1.messaging.schemas import v1_responses as rsm
from app.v1.messaging.schemas.v1_responses import V1MessageRequestResponse
from app.v1.users.deps.get_current_user import get_current_user
from app.container import ApplicationContainer
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.ports.services.file_service import FileServicePort
from src.messaging.application.use_cases.send_message import send_message_use_case
from src.messaging.application.use_cases.create_messaging_request_from_csv import (
    create_messaging_request_from_csv_use_case,
)
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


@router.post("/message")
async def message(
    request: rqm.V1MessageRequest,
    user: BaseUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        message_request_id, message_id = await send_message_use_case(
            session_id=request.session_id,
            phone_number=request.contact.phone_number,
            username=request.contact.username,
            user_id=request.contact.id,
            text=request.text,
            file_id=request.file_id,
            current_user_id=user.id,
            uow=uow,
        )
        await uow.commit()

        return {"message_request_id": message_request_id, "message_id": message_id}


@router.post("/message-requests/csv")
async def create_message_request_csv(
    session_id: int,
    file_id: int,
    title: str | None = None,
    default_text: str | None = None,
    default_sending_time: datetime | None = None,
    attachment_file_id: int | None = None,
    uow: AsyncUnitOfWork = Depends(get_uow),
    file_service: FileServicePort = Depends(get_file_service),
    user: BaseUser = Depends(get_current_user),
):
    async with uow:
        req = await create_messaging_request_from_csv_use_case(
            session_id=session_id,
            file_id=file_id,
            title=title,
            default_text=default_text,
            default_sending_time=default_sending_time,
            attachment_file_id=attachment_file_id,
            user_id=user.id,
            uow=uow,
            file_service=file_service,
        )
        await uow.commit()

    return {
        "id": req.id,
        "generated": req.generated,
        "request_file_id": req.request_file_id,
    }


@router.get("/message-requests/{message_request_id}")
async def get_message_request(
    message_request_id: int,
    user: BaseUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> V1MessageRequestResponse:
    async with uow:
        dto = await get_message_request_use_case(
            message_request_id=message_request_id,
            uow=uow,
        )

        return rsm.V1MessageRequestResponse(**dto.dump())


@router.post("/message-requests/import")
@inject
async def create_message_request_import(
    request: rqm.V1ImportMessageRequest,
    user: BaseUser = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
    import_staging_repo: ImportStagingRepositoryPort = Depends(
        Provide[ApplicationContainer.import_staging_repo]
    ),
):
    async with uow:
        result = await create_message_request_import_use_case(
            uow=uow,
            user_id=user.id,
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
        return result
