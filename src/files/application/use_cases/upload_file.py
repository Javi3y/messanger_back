from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
from uuid import uuid4

from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.domain.entities.file import File
from src.files.ports.services.file_service import FileServicePort
from src.files.ports.services.upload_port import UploadedFilePort


def _safe_name(filename: str | None) -> str:
    name = (filename or "blob.bin").strip()
    return Path(name).name or "blob.bin"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


async def upload_file_service(
    file_service: FileServicePort,
    uow: AsyncUnitOfWork,
    *,
    uploaded: UploadedFilePort,
    prefix: str = "uploads/",
    overwrite: bool = False,
    extra_meta: Mapping[str, str] | None = None,
) -> File:
    # ---- derive names/keys ----------------------------------------------------
    base_name = _safe_name(uploaded.filename())
    key_name = f"{_ts()}_{uuid4().hex}_{base_name}"

    # Let the storage adapter decide the final destination URI
    uri = file_service.build_uri(prefix=prefix, name=key_name)

    # ---- read payload ---------------------------------------------------------
    payload = await uploaded.read()
    content_type = uploaded.content_type() or "application/octet-stream"

    # ---- write to storage -----------------------------------------------------
    info = await file_service.write(
        uri=uri,
        data=payload,
        content_type=content_type,
        meta={"filename": base_name, **(extra_meta or {})},
        overwrite=overwrite,
    )
    # `info` is expected to expose: uri, size, etag, content_type (optional), modified_at (optional)

    # ---- persist entity -------------------------------------------------------
    entity = File(
        uri=info.uri,
        name=base_name,
        size=getattr(info, "size", None),
        content_type=getattr(info, "content_type", None) or content_type,
        etag=getattr(info, "etag", None),
        created_at=datetime.now(timezone.utc),
        modified_at=getattr(info, "modified_at", None),
        meta={"key": key_name, "prefix": prefix},
    )
    created = await uow.file_repo.add(entity=entity)

    created.download_url = file_service.build_download_url(uri=created.uri)

    return created
