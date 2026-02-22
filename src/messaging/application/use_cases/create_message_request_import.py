from datetime import UTC, datetime
from uuid import uuid4
from typing import Any

from src.base.application.services.outbox_service import OutboxService
from src.base.exceptions import NotFoundException
from src.messaging.domain.entities.messaging_request import MessagingRequest
from src.importing.application.outbox.events.bulk_import_stage_v1 import (
    BulkImportStageV1,
)
from src.importing.domain.enums.import_status import ImportStatus


async def create_message_request_import_use_case(
    *,
    uow,
    user_id: int,
    session_id: int,
    file_id: int,
    title: str | None,
    default_text: str | None,
    default_sending_time: datetime | None,
    attachment_file_id: int | None,
    import_config: dict[str, Any],
    ttl_seconds: int,
    import_staging_repo,
) -> dict[str, Any]:
    # validate session exists
    session = await uow.session_repo.get_by_id(id=session_id)
    if not session:
        raise NotFoundException(detail="Session not found")

    # validate file exists
    f = await uow.file_repo.get_by_id(id=file_id)
    if not f:
        raise NotFoundException(detail="File not found")

    # create message request
    req = MessagingRequest(
        user_id=user_id,
        session_id=session_id,
        request_file_id=file_id,
        attachment_file_id=attachment_file_id,
        title=title,
        sending_time=default_sending_time,
        default_text=default_text,
    )
    req = await uow.message_request_repo.add(entity=req)
    await uow.flush()

    job_key = f"message_request:{req.id}:{uuid4().hex}"

    # create staging job meta
    await import_staging_repo.create_job(
        job_key=job_key,
        meta={
            "status": str(ImportStatus.pending),
            "import_type": "message_request",
            "message_request_id": req.id,
            "file_id": file_id,
            "errors": [],
        },
        ttl_seconds=ttl_seconds,
    )

    outbox = OutboxService(uow)
    await outbox.publish(
        BulkImportStageV1(
            job_key=job_key,
            import_type="message_request",
            file_id=file_id,
            ttl_seconds=ttl_seconds,
            config=import_config,
            context={
                "user_id": user_id,
                "session_id": session_id,
                "message_request_id": req.id,
                "default_text": default_text,
                "default_sending_time": (
                    default_sending_time.isoformat() if default_sending_time else None
                ),
                "attachment_file_id": attachment_file_id,
            },
            dedup_key=f"bulk_import:{job_key}:stage",
            aggregate_type="bulk_import",
            aggregate_id=job_key,
            available_at=datetime.now(UTC),
        )
    )
    await uow.commit()

    return {"message_request_id": req.id, "job_key": job_key}
