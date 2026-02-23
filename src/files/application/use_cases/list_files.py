from src.base.exceptions import BadRequestException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.domain.dtos.file_dto import FileDTO
from src.files.ports.services.file_service import FileServicePort
from src.users.domain.entities.base_user import BaseUser


async def list_files_use_case(
    uow: AsyncUnitOfWork,
    file_service: FileServicePort,
    *,
    user: BaseUser,
    include_public: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[FileDTO]:
    requester_user_id = user.id
    if requester_user_id is None:
        raise BadRequestException(detail="User id is required")
    requester_user_id = int(requester_user_id)

    files = await uow.file_queries.list_files_with_owner(
        user_id=requester_user_id,
        include_public=include_public,
        limit=limit,
        offset=offset,
    )

    for file_dto in files:
        if not file_dto.download_url:
            file_dto.download_url = file_service.build_download_url(uri=file_dto.uri)

    return files
