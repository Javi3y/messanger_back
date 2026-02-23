from src.base.exceptions import NotFoundException, ForbiddenException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.domain.dtos.file_dto import FileDTO
from src.files.ports.services.file_service import FileServicePort
from src.users.domain.entities.base_user import BaseUser


async def get_file_use_case(
    uow: AsyncUnitOfWork,
    file_service: FileServicePort,
    *,
    id: int,
    user: BaseUser,
) -> FileDTO:
    if user.id is None:
        raise ForbiddenException(detail="User id is required")
    requester_user_id = int(user.id)

    file_dto = await uow.file_queries.get_file_with_owner(file_id=id)
    if not file_dto:
        raise NotFoundException(detail="File not found")

    if file_dto.owner_id is not None and file_dto.owner_id != requester_user_id:
        raise ForbiddenException(detail="You do not have access to this file")

    if not file_dto.download_url:
        file_dto.download_url = file_service.build_download_url(uri=file_dto.uri)

    return file_dto
