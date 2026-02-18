from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.container import ApplicationContainer
from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.messaging.application.registry.messenger_registry import MessengerRegistry


@inject
def get_cache_repo(
    cache_repo: AbstractCacheRepository = Depends(
        Provide[ApplicationContainer.cache_repo]
    ),
) -> AbstractCacheRepository:
    return cache_repo


@inject
def get_messenger_registry(
    registry: MessengerRegistry = Depends(
        Provide[ApplicationContainer.messenger_registry]
    ),
) -> MessengerRegistry:
    return registry
