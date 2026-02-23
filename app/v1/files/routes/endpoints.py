from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File as FormFile,
    Form,
)

from app.files.adapters.fastapi_upload_adapter import FastAPIUploadedFile
from app.deps.providers import get_file_service, get_uow
from app.v1.files.schemas import v1_responses as rsm
from app.v1.users.deps.get_current_user import get_current_user
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.ports.services.file_service import FileServicePort
from src.files.application.use_cases.get_file import (
    get_file_use_case,
)
from src.files.application.use_cases.list_files import list_files_use_case
from src.files.application.use_cases.upload_file import upload_file_use_case
from src.users.domain.entities.base_user import BaseUser

router = APIRouter(prefix="", tags=["files"])


@router.post("/upload", response_model=rsm.V1FileResponse)
async def upload_file(
    uploaded: UploadFile = FormFile(..., description="multipart file"),
    prefix: str = Form("uploads/", description="logical folder/prefix"),
    overwrite: bool = Form(False, description="allow overwrite if exists"),
    is_public: bool = Form(False, description="if true, file is public"),
    user: BaseUser = Depends(get_current_user),
    file_service: FileServicePort = Depends(get_file_service),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    uploaded_adapter = FastAPIUploadedFile(uploaded)

    async with uow:
        file_dto = await upload_file_use_case(
            file_service=file_service,
            uow=uow,
            user=user,
            uploaded=uploaded_adapter,
            is_public=is_public,
            prefix=prefix,
            overwrite=overwrite,
            extra_meta={"uploader": getattr(user, "username", "unknown")},
        )
        await uow.commit()

    return rsm.V1FileResponse(**file_dto.dump(exclude_none=True))


@router.get("/{file_id}", response_model=rsm.V1FileResponse)
async def get_file(
    file_id: int,
    user: BaseUser = Depends(get_current_user),
    file_service: FileServicePort = Depends(get_file_service),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        file_dto = await get_file_use_case(
            uow=uow,
            file_service=file_service,
            id=file_id,
            user=user,
        )
    return rsm.V1FileResponse(**file_dto.dump(exclude_none=True))


@router.get("", response_model=list[rsm.V1FileResponse])
async def list_files(
    include_public: bool = False,
    limit: int = 50,
    offset: int = 0,
    user: BaseUser = Depends(get_current_user),
    file_service: FileServicePort = Depends(get_file_service),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        file_dtos = await list_files_use_case(
            uow=uow,
            file_service=file_service,
            user=user,
            include_public=include_public,
            limit=limit,
            offset=offset,
        )

    return [
        rsm.V1FileResponse(**file_dto.dump(exclude_none=True)) for file_dto in file_dtos
    ]
