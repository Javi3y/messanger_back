from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.container import ApplicationContainer
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.base.infrastructure.lazy_entity_cache import LazyEntityCache
from src.files.ports.services.file_service import FileServicePort


@inject
def get_uow(
    uow: AsyncUnitOfWork = Depends(Provide[ApplicationContainer.unit_of_work]),
) -> AsyncUnitOfWork:
    return uow


@inject
def get_lazy_cache(
    lazy_cache: LazyEntityCache = Depends(
        Provide[ApplicationContainer.lazy_entity_cache]
    ),
) -> LazyEntityCache:
    return lazy_cache


@inject
def get_file_service(
    file_service: FileServicePort = Depends(Provide[ApplicationContainer.file_service]),
) -> FileServicePort:
    return file_service
