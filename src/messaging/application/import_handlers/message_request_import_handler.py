from datetime import datetime, timezone, UTC
from typing import Any

from src.base.application.services.outbox_service import OutboxService
from src.base.exceptions import BadRequestException
from src.importing.domain.dtos.base_import_config import BaseImportConfig
from src.importing.domain.enums.unknown_columns_policy import UnknownColumnsPolicy
from src.importing.ports.import_handler_port import ImportHandlerPort
from src.importing.ports.repositories.import_staging_repo_port import (
    ImportStagingRepositoryPort,
)
from src.importing.ports.services.tabular_reader_port import TabularDocument
from src.messaging.application.outbox.events.request_ready_to_send_v1 import (
    MessageRequestReadyToSendV1,
)
from src.messaging.domain.entities.message import Message

from src.messaging.application.import_handlers.message_request_import_config import (
    MessageRequestImportConfig,
)


def _canon(s: str) -> str:
    return (s or "").strip().casefold()


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).astimezone(timezone.utc)
        return value.astimezone(timezone.utc)

    v = str(value).strip()
    if not v:
        return None
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class MessageRequestImportHandler(ImportHandlerPort):
    def validate_config(self, *, config: BaseImportConfig) -> None:
        if not isinstance(config, MessageRequestImportConfig):
            raise ValueError("Invalid config type for message_request import")

        # enforce allowed internal keys (so config can't drift)
        allowed = {"phone_number", "username", "user_id", "text", "sending_time"}
        bad_required = set(config.required.keys()) - allowed
        bad_optional = set(config.optional.keys()) - allowed
        if bad_required or bad_optional:
            raise BadRequestException(
                detail=f"Invalid column keys: {sorted(bad_required | bad_optional)}"
            )

        if "phone_number" not in config.required:
            raise BadRequestException(
                detail="phone_number must be required for message_request import (for now)"
            )

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
        assert isinstance(config, MessageRequestImportConfig)
        unknown_columns_policy = config.unknown_columns_policy

        headers = doc.headers
        header_map = {_canon(h): h for h in headers}

        def _get(row: dict[str, Any], header_name: str | None) -> Any:
            if not header_name:
                return None
            actual = header_map.get(_canon(header_name))
            if not actual:
                return None
            return row.get(actual)

        staged_rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        total = 0
        ok = 0
        failed = 0

        declared_headers = config.all_declared_headers()
        declared_canon = {_canon(h) for h in declared_headers}

        for r in doc.rows:
            total += 1
            raw = r.values

            normalized: dict[str, Any] = {}
            row_errors: list[str] = []

            phone = _get(raw, config.required.get("phone_number"))
            phone_str = (str(phone).strip() if phone is not None else "") or None
            if not phone_str:
                row_errors.append("phone_number is required")

            username = _get(raw, config.optional.get("username"))
            user_id = _get(raw, config.optional.get("user_id"))
            text = _get(raw, config.optional.get("text"))
            sending_time = _get(raw, config.optional.get("sending_time"))

            if username is not None:
                normalized["username"] = str(username).strip() or None
            if user_id is not None:
                normalized["user_id"] = str(user_id).strip() or None
            normalized["phone_number"] = phone_str

            if text is not None:
                normalized["text"] = str(text).strip() or None

            try:
                dt = _parse_dt(sending_time)
                if dt is not None:
                    normalized["sending_time"] = dt.isoformat()
            except Exception:
                row_errors.append("sending_time is invalid (expected ISO8601)")

            # extras (explicit mapping)
            extras: dict[str, Any] = {}
            for var, header in config.extras.items():
                extras[var] = _get(raw, header)

            if unknown_columns_policy == UnknownColumnsPolicy.capture:
                for h, v in raw.items():
                    if _canon(h) in declared_canon:
                        continue
                    extras[h] = v

            staged = {
                "row_number": r.row_number,
                "raw": raw,
                "normalized": normalized,
                "extras": extras,
                "errors": row_errors,
            }

            if row_errors:
                failed += 1
                if len(errors) < config.max_errors:
                    errors.append({"row": r.row_number, "errors": row_errors})
                if config.stop_on_row_error:
                    # stage nothing further and mark failed
                    await staging_repo.add_errors(
                        job_key=job_key,
                        errors=errors,
                        ttl_seconds=ttl_seconds,
                        max_errors=config.max_errors,
                    )
                    raise BadRequestException(
                        detail=f"Row error at row {r.row_number}: {row_errors}"
                    )
            else:
                ok += 1

            staged_rows.append(staged)

            # flush in chunks
            if len(staged_rows) >= 500:
                await staging_repo.push_rows(
                    job_key=job_key, rows=staged_rows, ttl_seconds=ttl_seconds
                )
                staged_rows.clear()

        if staged_rows:
            await staging_repo.push_rows(
                job_key=job_key, rows=staged_rows, ttl_seconds=ttl_seconds
            )

        if errors:
            await staging_repo.add_errors(
                job_key=job_key,
                errors=errors,
                ttl_seconds=ttl_seconds,
                max_errors=config.max_errors,
            )

        await staging_repo.update_meta(
            job_key=job_key,
            updates={"total_rows": total, "staged_rows": ok, "failed_rows": failed},
            ttl_seconds=ttl_seconds,
        )
        return {"total": total, "staged": ok, "failed": failed}

    async def process(
        self,
        *,
        uow,
        job_key: str,
        context: dict[str, Any],
        staging_repo: ImportStagingRepositoryPort,
        batch_size: int,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        # message_request_id + defaults come from context
        message_request_id = context.get("message_request_id")
        if not message_request_id:
            raise BadRequestException(detail="message_request_id missing in context")

        default_text = (context.get("default_text") or "").strip()
        default_sending_time = context.get("default_sending_time")  # iso string or None
        attachment_file_id = context.get("attachment_file_id")

        earliest: datetime | None = None
        created = 0
        skipped = 0
        bad = 0

        while True:
            batch = await staging_repo.pop_rows(job_key=job_key, limit=batch_size)
            if not batch:
                break

            for item in batch:
                errs = item.get("errors") or []
                if errs:
                    bad += 1
                    continue

                n = item.get("normalized") or {}

                txt = (n.get("text") or "").strip() or default_text
                if not txt:
                    skipped += 1
                    continue

                sending_time = None
                if n.get("sending_time"):
                    sending_time = datetime.fromisoformat(n["sending_time"])
                elif default_sending_time:
                    sending_time = datetime.fromisoformat(default_sending_time)

                msg = Message(
                    message_request_id=int(message_request_id),
                    phone_number=n.get("phone_number"),
                    username=n.get("username"),
                    user_id=n.get("user_id"),
                    text=txt,
                    attachment_file_id=attachment_file_id,
                    sending_time=sending_time,
                )
                if earliest is None or msg.sending_time < earliest:
                    earliest = msg.sending_time

                await uow.message_repo.add(entity=msg)
                created += 1

            await uow.commit()

        # publish downstream "ready to send"
        outbox = OutboxService(uow)
        await outbox.publish(
            MessageRequestReadyToSendV1(
                message_request_id=int(message_request_id),
                available_at=earliest or datetime.now(UTC),
                dedup_key=f"messaging_request:{message_request_id}:send",
                aggregate_type="messaging_request",
                aggregate_id=str(message_request_id),
            )
        )
        await uow.commit()

        return {"created": created, "skipped": skipped, "bad_rows": bad}
