from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.base.exceptions import NotFoundException
from src.files.domain.entities.file import File
from src.files.ports.services.file_service import FileServicePort


async def get_file_service(
    uow: AsyncUnitOfWork,
    file_service: FileServicePort,
    *,
    id: int,
) -> File:
    f = await uow.file_repo.get_by_id(id=id)
    if not f:
        raise NotFoundException(entity=File)

    if not getattr(f, "download_url", None):
        f.download_url = file_service.build_download_url(uri=f.uri)

    return f
