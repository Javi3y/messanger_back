from dataclasses import dataclass
from typing import AsyncIterator, Mapping, Tuple
from datetime import datetime, timezone
import re
import asyncio
import unicodedata

import os
import uuid


import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.files.ports.services.file_service import (
    FileServicePort,
    FileInfo,
)
from src.files.domain.exceptions.exceptions import (
    FileServiceError,
    NotFoundError,
    ConflictError,
)

_S3_URI = re.compile(r"^s3://(?P<bucket>[^/]+)/?(?P<key>.*)$")


def _parse_s3_uri(uri: str) -> Tuple[str, str]:
    """Return (bucket, key) from an s3:// URI."""
    m = _S3_URI.match(uri)
    if not m:
        raise FileServiceError(f"Invalid S3 URI: {uri!r}")
    return m.group("bucket"), m.group("key")


def _utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _make_safe_s3_key(original_name: str, prefix: str = "uploads/") -> str:
    # Split extension
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()

    # Normalize base name
    base = os.path.splitext(original_name)[0]
    safe_base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)

    if not safe_base:
        safe_base = uuid.uuid4().hex

    # Limit length (S3 safe, DO Spaces safe)
    MAX_BASE_LEN = 100  # adjust if needed
    if len(safe_base) > MAX_BASE_LEN:
        safe_base = safe_base[:MAX_BASE_LEN]

    filename = safe_base + ext

    return f"{prefix}{filename}"


@dataclass(frozen=True)
class S3Settings:
    endpoint: str | None = None
    region: str | None = "us-east-1"
    access_key: str | None = None
    secret_key: str | None = None
    use_ssl: bool = False
    path_style: bool = True
    default_bucket: str | None = None
    public_base_url: str | None = None
    presign_ttl: int = 300


class S3FileService(FileServicePort):
    def __init__(self, settings: S3Settings):
        self._settings = settings
        # Keep a single session; clients are created per-op
        self._session = aioboto3.Session()

        self._config = Config(
            region_name=settings.region,
            s3={
                "addressing_style": "path" if settings.path_style else "virtual",
            },
            retries={"max_attempts": 3, "mode": "standard"},
        )

        self._client_kwargs = {
            "endpoint_url": settings.endpoint,
            "aws_access_key_id": settings.access_key,
            "aws_secret_access_key": settings.secret_key,
            "use_ssl": settings.use_ssl,
            "config": self._config,
        }

    # -------------------------
    # Read
    # -------------------------

    async def read(self, uri: str) -> bytes:
        bucket, key = _parse_s3_uri(uri)
        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                resp = await s3.get_object(Bucket=bucket, Key=key)
                body = await resp["Body"].read()
                return body
        except ClientError as e:
            _raise_from_client_error(e, uri)

    async def stream(
        self, uri: str, chunk_size: int = 1024 * 1024
    ) -> AsyncIterator[bytes]:
        bucket, key = _parse_s3_uri(uri)
        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                resp = await s3.get_object(Bucket=bucket, Key=key)
                stream = resp["Body"]
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except ClientError as e:
            _raise_from_client_error(e, uri)

    # -------------------------
    # Write
    # -------------------------

    async def write(
        self,
        uri: str,
        data: bytes,
        *,
        content_type: str | None = None,
        meta: Mapping[str, str] | None = None,
        overwrite: bool = True,
    ) -> FileInfo:
        bucket, key = _parse_s3_uri(uri)

        def _ascii_safe(value: str) -> str:
            return (
                unicodedata.normalize("NFKD", value)
                .encode("ascii", "ignore")
                .decode("ascii")
            )

        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                if not overwrite:
                    # Fail if object already exists
                    try:
                        await s3.head_object(Bucket=bucket, Key=key)
                        raise ConflictError(f"Object already exists at {uri}")
                    except ClientError as head_err:
                        if _is_not_found(head_err):
                            pass
                        else:
                            _raise_from_client_error(head_err, uri)

                extra: dict = {}
                if content_type:
                    extra["ContentType"] = content_type
                if meta:
                    safe_meta = {}
                    for k, v in meta.items():
                        if isinstance(v, str):
                            safe_meta[k] = _ascii_safe(v)
                        else:
                            safe_meta[k] = _ascii_safe(str(v))
                    extra["Metadata"] = safe_meta

                await s3.put_object(Bucket=bucket, Key=key, Body=data, **extra)

                # Read back minimal head to build FileInfo
                head = await s3.head_object(Bucket=bucket, Key=key)
                return FileInfo(
                    uri=uri,
                    size=head.get("ContentLength"),
                    content_type=head.get("ContentType"),
                    etag=_strip_quotes(head.get("ETag")),
                    modified_at=_utc(head.get("LastModified")),
                )
        except ClientError as e:
            _raise_from_client_error(e, uri)

    def build_uri(self, *, prefix: str, name: str) -> str:
        if not self._settings.default_bucket:
            raise RuntimeError("S3 default bucket is not configured")

        safe_key = _make_safe_s3_key(name, prefix=f"{prefix.strip('/')}/")

        return f"s3://{self._settings.default_bucket}/{safe_key}"

    def build_download_url(self, *, uri: str) -> str:
        base = getattr(self._settings, "public_base_url", None)
        if base:
            _, rest = uri.split("://", 1)
            _bucket, key = rest.split("/", 1)
            # URL encode ONLY for browser compatibility
            from urllib.parse import quote

            return f"{base.rstrip('/')}/{quote(key, safe='')}"

        # Presign using boto client
        bucket, key = _parse_s3_uri(uri)

        async def _presign() -> str:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                return await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=self._settings.presign_ttl,
                )

        return asyncio.get_event_loop().run_until_complete(_presign())

    # -------------------------
    # Meta / mgmt
    # -------------------------

    async def delete(self, uri: str, *, missing_ok: bool = True) -> None:
        bucket, key = _parse_s3_uri(uri)
        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                await s3.delete_object(Bucket=bucket, Key=key)
        except ClientError as e:
            if _is_not_found(e) and missing_ok:
                return
            _raise_from_client_error(e, uri)

    async def exists(self, uri: str) -> bool:
        bucket, key = _parse_s3_uri(uri)
        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                await s3.head_object(Bucket=bucket, Key=key)
                return True
        except ClientError as e:
            if _is_not_found(e):
                return False
            _raise_from_client_error(e, uri)

    async def stat(self, uri: str) -> FileInfo:
        bucket, key = _parse_s3_uri(uri)
        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                head = await s3.head_object(Bucket=bucket, Key=key)
                return FileInfo(
                    uri=uri,
                    size=head.get("ContentLength"),
                    content_type=head.get("ContentType"),
                    etag=_strip_quotes(head.get("ETag")),
                    modified_at=_utc(head.get("LastModified")),
                )
        except ClientError as e:
            _raise_from_client_error(e, uri)

    # -------------------------
    # Listing
    # -------------------------

    async def list(
        self, prefix: str, *, recursive: bool = False
    ) -> AsyncIterator[FileInfo]:
        """
        prefix must be s3://bucket/some/prefix
        If recursive=False, only yields objects directly under the prefix (no delimiter).
        """
        bucket, key_prefix = _parse_s3_uri(prefix)
        try:
            async with self._session.client("s3", **self._client_kwargs) as s3:
                paginator = s3.get_paginator("list_objects_v2")
                # For "non-recursive", we emulate directory behavior using Delimiter="/"
                pagination_cfg = {
                    "Bucket": bucket,
                    "Prefix": key_prefix,
                }
                if not recursive:
                    pagination_cfg["Delimiter"] = "/"

                async for page in paginator.paginate(**pagination_cfg):
                    for obj in page.get("Contents", []):
                        yield FileInfo(
                            uri=f"s3://{bucket}/{obj['Key']}",
                            size=obj.get("Size"),
                            etag=_strip_quotes(obj.get("ETag")),
                            modified_at=_utc(obj.get("LastModified")),
                            content_type=None,  # need head_object if you require content-type
                        )
        except ClientError as e:
            _raise_from_client_error(e, prefix)


# -------------------------
# Error helpers
# -------------------------


def _is_not_found(e: ClientError) -> bool:
    code = (e.response or {}).get("Error", {}).get("Code")
    return (
        code in {"404", "NoSuchKey", "NotFound"}
        or e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404
    )


def _strip_quotes(etag: str | None) -> str | None:
    if not etag:
        return None
    return etag.strip('"')


def _raise_from_client_error(e: ClientError, uri: str) -> None:
    if _is_not_found(e):
        raise NotFoundError(f"Object not found: {uri}") from e
    code = (e.response or {}).get("Error", {}).get("Code")
    if code in {"PreconditionFailed"}:
        raise ConflictError(f"Conflict writing object: {uri}") from e
    raise FileServiceError(f"S3 error for {uri}: {code}") from e
