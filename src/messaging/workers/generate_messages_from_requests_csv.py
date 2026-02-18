import csv
import io
import logging
from datetime import datetime, timezone

from src.base.application.services.outbox_service import OutboxService
from src.messaging.application.outbox.events.request_ready_to_send_v1 import (
    MessageRequestReadyToSendV1,
)
from src.messaging.domain.entities.message import Message
from src.messaging.domain.entities.messaging_request import MessagingRequest

logger = logging.getLogger(__name__)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None

    v = value.strip()
    if not v:
        return None

    # Accept ISO strings that end with "Z"
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"

    dt = datetime.fromisoformat(v)

    # If tz-naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _decode_csv_bytes(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1256", "windows-1256", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


async def generate_messages_from_requests_csv(
    *,
    uow_factory,
    file_service,
    batch_size: int = 10,
) -> dict[str, int]:
    created = 0
    skipped = 0

    async with uow_factory() as uow:
        reqs: list[MessagingRequest] = await uow.message_request_repo.get_not_generated(
            limit=batch_size,
            lock=True,
            skip_locked=True,
        )

        if not reqs:
            return {"created": 0, "skipped": 0}

        for req in reqs:
            if not req.request_file_id:
                skipped += 1
                continue

            f = await uow.file_repo.get_by_id(id=req.request_file_id)
            data = await file_service.read(f.uri)

            csv_text = _decode_csv_bytes(data)

            buf = io.StringIO(csv_text, newline="")
            reader = csv.DictReader(buf)

            if not reader.fieldnames:
                logger.warning(
                    req.id,
                    req.request_file_id,
                )
                skipped += 1
                req.generated = True
                await uow.message_request_repo.update(entity=req)
                continue

            earliest: datetime | None = None

            for row in reader:
                if not row:
                    skipped += 1
                    continue

                msg_text = (row.get("text") or "").strip() or (
                    req.default_text or ""
                ).strip()
                if not msg_text:
                    skipped += 1
                    continue

                msg = Message(
                    message_request_id=req.id,
                    phone_number=(row.get("phone_number") or "").strip() or None,
                    username=(row.get("username") or "").strip() or None,
                    user_id=(row.get("user_id") or "").strip() or None,
                    text=msg_text,
                    attachment_file_id=req.attachment_file_id or None,
                    sending_time=_parse_dt(row.get("sending_time")) or req.sending_time,
                )

                if earliest is None or msg.sending_time < earliest:
                    earliest = msg.sending_time

                await uow.message_repo.add(entity=msg)
                created += 1

            req.generated = True
            await uow.message_request_repo.update(entity=req)

            outbox = OutboxService(uow)
            await outbox.publish(
                MessageRequestReadyToSendV1(
                    message_request_id=req.id,
                    available_at=earliest or req.sending_time,
                    dedup_key=f"messaging_request:{req.id}:send",
                    aggregate_type="messaging_request",
                    aggregate_id=str(req.id),
                )
            )

        await uow.commit()

    return {"created": created, "skipped": skipped}
