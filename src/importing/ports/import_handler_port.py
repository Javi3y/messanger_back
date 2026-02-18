from abc import ABC, abstractmethod
from typing import Any

from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.importing.domain.dtos.base_import_config import BaseImportConfig
from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)
from src.importing.ports.services.tabular_reader_port import TabularDocument


class ImportHandlerPort(ABC):
    @abstractmethod
    def validate_config(self, *, config: BaseImportConfig) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stage(
        self,
        *,
        job_key: str,
        doc: TabularDocument,
        config: BaseImportConfig,
        context: dict[str, Any],
        staging_repo: ImportStagingRepositoryPort,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def process(
        self,
        *,
        uow: AsyncUnitOfWork,
        job_key: str,
        context: dict[str, Any],
        staging_repo: ImportStagingRepositoryPort,
        batch_size: int,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        raise NotImplementedError
