from datetime import datetime, UTC

from src.base.application.services.outbox_service import OutboxService
from src.base.exceptions import BadRequestException
from src.files.ports.services.file_service import FileServicePort
from src.importing.application.registry.import_registry import ImportRegistry
from src.importing.application.outbox.events.bulk_import_stage_v1 import (
    BulkImportStageV1,
)
from src.importing.application.outbox.events.bulk_import_process_v1 import (
    BulkImportProcessV1,
)
from src.importing.domain.enums.import_status import ImportStatus
from src.importing.domain.enums.unknown_columns_policy import UnknownColumnsPolicy
from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)
from src.importing.ports.services.tabular_reader_port import TabularReaderPort


def _canon(s: str) -> str:
    return (s or "").strip().casefold()


async def handle_bulk_import_stage_v1(
    *,
    uow,
    event: BulkImportStageV1,
    file_service: FileServicePort,
    tabular_reader: TabularReaderPort,
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

    config = config_cls(**event.config)
    unknown_columns_policy = config.unknown_columns_policy
    try:
        config.validate_basic()
    except Exception as e:
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={
                "status": str(ImportStatus.failed),
                "error_message": f"Invalid config: {e}",
            },
            ttl_seconds=event.ttl_seconds,
        )
        return

    # mark staging
    await import_staging_repo.update_meta(
        job_key=event.job_key,
        updates={"status": str(ImportStatus.staging), "import_type": event.import_type},
        ttl_seconds=event.ttl_seconds,
    )

    # load file record + bytes
    f = await uow.file_repo.get_by_id(id=event.file_id)
    if not f:
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={
                "status": str(ImportStatus.failed),
                "error_message": f"File not found: {event.file_id}",
            },
            ttl_seconds=event.ttl_seconds,
        )
        return

    content = await file_service.read(uri=f.uri)
    doc = tabular_reader.read(
        filename=f.name,
        content_type=f.content_type,
        content=content,
    )

    if not doc.headers:
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={
                "status": str(ImportStatus.failed),
                "error_message": "No headers found in file",
            },
            ttl_seconds=event.ttl_seconds,
        )
        return

    # header validation
    actual_headers = doc.headers
    actual_map = {_canon(h): h for h in actual_headers}

    required_headers = [config.required[k] for k in config.required]
    missing_required = [h for h in required_headers if _canon(h) not in actual_map]

    declared = config.all_declared_headers()
    unknown = [
        h for h in actual_headers if _canon(h) not in {_canon(x) for x in declared}
    ]

    if missing_required:
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={
                "status": str(ImportStatus.failed),
                "error_message": "Missing required columns",
                "missing_columns": missing_required,
            },
            ttl_seconds=event.ttl_seconds,
        )
        return

    if unknown and unknown_columns_policy == UnknownColumnsPolicy.error:
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={
                "status": str(ImportStatus.failed),
                "error_message": "Unknown columns present",
                "unknown_columns": unknown,
            },
            ttl_seconds=event.ttl_seconds,
        )
        return

    # stage using handler
    handler = handler_cls()
    try:
        handler.validate_config(config=config)
        stats = await handler.stage(
            job_key=event.job_key,
            doc=doc,
            config=config,
            context=event.context,
            staging_repo=import_staging_repo,
            ttl_seconds=event.ttl_seconds,
        )
    except (BadRequestException, ValueError) as e:
        # deterministic -> mark failed, no retry
        await import_staging_repo.update_meta(
            job_key=event.job_key,
            updates={"status": str(ImportStatus.failed), "error_message": str(e)},
            ttl_seconds=event.ttl_seconds,
        )
        return

    await import_staging_repo.update_meta(
        job_key=event.job_key,
        updates={"status": str(ImportStatus.staged), "stage_stats": stats},
        ttl_seconds=event.ttl_seconds,
    )

    # chain processing (async)
    outbox = OutboxService(uow)
    await outbox.publish(
        BulkImportProcessV1(
            job_key=event.job_key,
            import_type=event.import_type,
            batch_size=200,
            ttl_seconds=event.ttl_seconds,
            context=event.context,
            dedup_key=f"bulk_import:{event.job_key}:process",
            aggregate_type="bulk_import",
            aggregate_id=event.job_key,
            available_at=datetime.now(UTC),
        )
    )
