from src.importing.application.registry.import_registry import ImportRegistry
from src.importing.application.outbox.events.bulk_import_process_v1 import (
    BulkImportProcessV1,
)
from src.importing.domain.enums.import_status import ImportStatus
from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)


async def handle_bulk_import_process_v1(
    *,
    uow,
    event: BulkImportProcessV1,
    import_staging_repo: ImportStagingRepositoryPort,
    import_registry: ImportRegistry,
) -> None:
    handler_cls = import_registry.get_handler(import_type=event.import_type)
    config_cls = import_registry.get_config(import_type=event.import_type)
    if not handler_cls or not config_cls:
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={
                "status": str(ImportStatus.failed),
                "error_message": f"Unknown import_type: {event.import_type}",
            },
            ttl_seconds=event.ttl_seconds,
        )
        return

    await import_staging_repo.update_meta(
        job_key=event.job_key,
        updates={"status": str(ImportStatus.processing)},
        ttl_seconds=event.ttl_seconds,
    )

    handler = handler_cls()
    stats = await handler.process(
        uow=uow,
        job_key=event.job_key,
        context=event.context,
        staging_repo=import_staging_repo,
        batch_size=event.batch_size,
        ttl_seconds=event.ttl_seconds,
    )

    await import_staging_repo.update_meta(
        job_key=event.job_key,
        updates={"status": str(ImportStatus.completed), "process_stats": stats},
        ttl_seconds=event.ttl_seconds,
    )
    await import_staging_repo.cleanup(job_key=event.job_key)
