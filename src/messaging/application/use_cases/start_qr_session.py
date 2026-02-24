import io
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from uuid import uuid4

import qrcode

from src.base.exceptions import BadRequestException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.files.domain.dtos.file_dto import FileDTO
from src.files.domain.entities.file import File
from src.files.ports.services.file_service import FileServicePort
from src.messaging.application.registry.messenger_registry import MessengerRegistry
from src.messaging.domain.dtos.session_dto import SessionDTO
from src.messaging.domain.dtos.start_qr_session_dto import StartQrSessionDTO
from src.messaging.domain.entities.session import Session
from src.messaging.domain.enums.messenger_type import MessengerType
from src.messaging.ports.messengers.capabilities.auth.qr import QrAuthPort
from src.users.domain.entities.base_user import BaseUser


def _safe_name(filename: str) -> str:
    return Path(filename.strip() or "blob.bin").name or "blob.bin"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


async def start_qr_session_use_case(
    *,
    title: str,
    phone_number: str,
    messenger_type: MessengerType,
    uow: AsyncUnitOfWork,
    user: BaseUser,
    registry: MessengerRegistry,
    file_service: FileServicePort,
) -> StartQrSessionDTO:
    user_id = user.id
    if user_id is None:
        raise BadRequestException(detail="User id is required")
    user_id = cast(int, user_id)

    messenger = registry.get_messenger(messenger_type)
    if not isinstance(messenger, QrAuthPort):
        raise BadRequestException(
            detail=f"Messenger {messenger_type.value} does not support QR login"
        )

    session = Session(
        user_id=user_id,
        title=title,
        session_type=messenger_type,
        phone_number=phone_number,
        is_active=False,
    )
    session = await uow.session_repo.add(entity=session)
    await uow.flush()

    await messenger.set_session(session)
    qr_code = await messenger.login()

    qr_image = qrcode.make(qr_code)
    qr_buffer = io.BytesIO()
    qr_image.save(qr_buffer)

    base_name = _safe_name(f"whatsapp-qr-session-{session.id}.png")
    key_name = f"{_ts()}_{uuid4().hex}_{base_name}"
    uri = file_service.build_uri(prefix="qr/", name=key_name)
    info = await file_service.write(
        uri=uri,
        data=qr_buffer.getvalue(),
        content_type="image/png",
        meta={
            "filename": base_name,
            "kind": "whatsapp_qr",
            "session_id": str(session.id),
        },
        overwrite=True,
    )

    qr_file = File(
        uri=info.uri,
        name=base_name,
        size=getattr(info, "size", None),
        content_type=getattr(info, "content_type", None) or "image/png",
        etag=getattr(info, "etag", None),
        created_at=datetime.now(timezone.utc),
        modified_at=getattr(info, "modified_at", None),
        meta={
            "key": key_name,
            "prefix": "qr/",
            "kind": "whatsapp_qr",
            "session_id": str(session.id),
            "messenger_type": messenger_type.value,
        },
        user_id=user_id,
    )
    qr_file = await uow.file_repo.add(entity=qr_file)

    if session.id is None:
        raise BadRequestException(detail="Session id is required")
    if qr_file.id is None:
        raise BadRequestException(detail="File id is required")

    session_dto = SessionDTO(
        id=int(session.id),
        title=session.title,
        phone_number=session.phone_number,
        session_type=session.session_type.value,
        is_active=session.is_active,
        user_id=session.user_id,
    )
    file_dto = FileDTO.from_file(
        file=qr_file,
        user=user,
        download_url=file_service.build_download_url(uri=qr_file.uri),
    )

    return StartQrSessionDTO(
        session=session_dto,
        file=file_dto,
    )
