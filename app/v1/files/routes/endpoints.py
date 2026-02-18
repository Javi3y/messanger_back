from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File as FormFile,
    Form,
    HTTPException,
)

from app.files.adapters.fastapi_upload_adapter import FastAPIUploadedFile
from app.deps.providers import get_file_service, get_uow
from app.v1.files.schemas import v1_responses as rsm
from app.v1.users.deps.get_current_user import get_current_user
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.ports.services.file_service import FileServicePort
from src.files.application.use_cases.get_file import (
    get_file_service as use_case_get_file,
)
from src.files.application.use_cases.upload_file import upload_file_service
from src.users.domain.entities.base_user import BaseUser

router = APIRouter(prefix="", tags=["files"])


@router.post("/upload", response_model=rsm.V1FileResponse)
async def upload_file(
    uploaded: UploadFile = FormFile(..., description="multipart file"),
    prefix: str = Form("uploads/", description="logical folder/prefix"),
    overwrite: bool = Form(False, description="allow overwrite if exists"),
    user: BaseUser = Depends(get_current_user),
    file_service: FileServicePort = Depends(get_file_service),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    uploaded_adapter = FastAPIUploadedFile(uploaded)

    async with uow:
        created = await upload_file_service(
            file_service=file_service,
            uow=uow,
            uploaded=uploaded_adapter,
            prefix=prefix,
            overwrite=overwrite,
            extra_meta={"uploader": getattr(user, "username", "unknown")},
        )
        await uow.commit()

    if not created.download_url:
        raise HTTPException(status_code=500, detail="Download URL is not configured")

    return rsm.V1FileResponse(
        id=created.id,
        uri=created.uri,
        name=created.name,
        size=created.size,
        content_type=created.content_type,
        etag=created.etag,
        created_at=created.created_at,
        modified_at=created.modified_at,
        meta=created.meta,
        download_url=created.download_url,
    )


@router.get("/{file_id}", response_model=rsm.V1FileResponse)
async def get_file(
    file_id: int,
    user: BaseUser = Depends(get_current_user),
    file_service: FileServicePort = Depends(get_file_service),
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    async with uow:
        f = await use_case_get_file(
            uow=uow,
            file_service=file_service,
            id=file_id,
        )

    return rsm.V1FileResponse(
        id=f.id,
        uri=f.uri,
        name=f.name,
        size=f.size,
        content_type=f.content_type,
        etag=f.etag,
        created_at=f.created_at,
        modified_at=f.modified_at,
        meta=f.meta,
        download_url=f.download_url or "",
    )
