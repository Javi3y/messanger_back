import asyncio
import io
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Mapping
from urllib.parse import unquote, urlparse

from src.files.ports.services.file_service import (
    FileServicePort,
    FileInfo,
)
from src.files.domain.exceptions.exceptions import (
    FileServiceError,
    NotFoundError,
    ConflictError,
)


@dataclass(frozen=True)
class LocalFSSettings:
    root: Path | None = None
    allow_outside_root: bool = False
    base_url: str | None = None


class LocalDirectoryFileService(FileServicePort):

    def __init__(self, settings: LocalFSSettings = LocalFSSettings()):
        self._settings = settings
        if self._settings.root is not None:
            # Normalize root to absolute, resolved path
            object.__setattr__(self._settings, "root", self._settings.root.resolve())

    # -------------------------
    # Read
    # -------------------------

    async def read(self, uri: str) -> bytes:
        path = self._path_from_file_uri(uri)
        await self._ensure_exists_file(path, uri)
        return await asyncio.to_thread(path.read_bytes)

    async def stream(
        self, uri: str, chunk_size: int = 1024 * 1024
    ) -> AsyncIterator[bytes]:
        path = self._path_from_file_uri(uri)
        await self._ensure_exists_file(path, uri)

        def _open() -> io.BufferedReader:
            return open(path, "rb")

        f = await asyncio.to_thread(_open)
        try:
            while True:
                chunk = await asyncio.to_thread(f.read, chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            await asyncio.to_thread(f.close)

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
        path = self._path_from_file_uri(uri)
        parent = path.parent

        def _prepare_and_write():
            parent.mkdir(parents=True, exist_ok=True)
            if not overwrite and path.exists():
                raise ConflictError(f"Object already exists at {uri}")
            with open(path, "wb") as f:
                f.write(data)

        try:
            await asyncio.to_thread(_prepare_and_write)
        except ConflictError:
            # pass through domain conflict
            raise
        except Exception as e:
            raise FileServiceError(f"Failed to write {uri}: {e}") from e

        return await self.stat(uri)

    # -------------------------
    # Meta / mgmt
    # -------------------------

    async def delete(self, uri: str, *, missing_ok: bool = True) -> None:
        path = self._path_from_file_uri(uri)

        def _delete():
            if path.exists():
                if path.is_dir():
                    # Only files are deletable via this service
                    raise FileServiceError(
                        f"Refusing to delete directory via file API: {uri}"
                    )
                path.unlink()
            else:
                if not missing_ok:
                    raise NotFoundError(f"Object not found: {uri}")

        try:
            await asyncio.to_thread(_delete)
        except NotFoundError:
            raise
        except Exception as e:
            raise FileServiceError(f"Failed to delete {uri}: {e}") from e

    async def exists(self, uri: str) -> bool:
        path = self._path_from_file_uri(uri)
        return await asyncio.to_thread(lambda: path.exists() and path.is_file())

    async def stat(self, uri: str) -> FileInfo:
        path = self._path_from_file_uri(uri)
        await self._ensure_exists_file(path, uri)

        def _stat() -> FileInfo:
            st = path.stat()
            # Best-effort MIME type
            ctype, _ = mimetypes.guess_type(str(path))
            return FileInfo(
                uri=uri,
                size=st.st_size,
                content_type=ctype,
                etag=None,  # not computed for local FS (avoid hashing large files)
                modified_at=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
            )

        try:
            return await asyncio.to_thread(_stat)
        except Exception as e:
            raise FileServiceError(f"Failed to stat {uri}: {e}") from e

    # -------------------------
    # Listing
    # -------------------------

    async def list(
        self, prefix: str, *, recursive: bool = False
    ) -> AsyncIterator[FileInfo]:
        root_dir = self._path_from_file_uri(prefix)
        if not await asyncio.to_thread(root_dir.exists):
            raise NotFoundError(f"Directory not found: {prefix}")
        if not await asyncio.to_thread(root_dir.is_dir):
            raise FileServiceError(f"Not a directory: {prefix}")

        if not recursive:
            # Non-recursive: one level using scandir
            for fi in await asyncio.to_thread(lambda: list(os.scandir(root_dir))):
                if fi.is_file():
                    yield await self._fileinfo_from_path(Path(fi.path))
        else:
            # Recursive: walk
            for dirpath, _dirs, files in await asyncio.to_thread(
                lambda: list(os.walk(root_dir))
            ):
                for name in files:
                    yield await self._fileinfo_from_path(Path(dirpath) / name)

    def build_uri(self, *, prefix: str, name: str) -> str:
        root = self._settings.root
        if not root:
            raise RuntimeError("Local root_dir is not configured")
        path = os.path.join(str(root), prefix.strip("/"), name)
        return f"file://{os.path.abspath(path)}"

    def build_download_url(self, *, uri: str) -> str:
        base_url = getattr(self._settings, "base_url", None)
        if not base_url:
            raise RuntimeError(
                "Local adapter needs settings.base_url for public serving (nginx)."
            )

        # file://<abs path>
        path = Path(uri.replace("file://", "")).resolve()
        root = Path(self._settings.root).resolve()
        rel = path.relative_to(root)
        return f"{base_url.rstrip('/')}/{str(rel).replace('\\', '/')}"

    # -------------------------
    # Helpers
    # -------------------------

    async def _fileinfo_from_path(self, path: Path) -> FileInfo:
        # Build a file:// URI from the absolute path
        abs_path = await asyncio.to_thread(path.resolve)
        # On Windows, Path.as_posix will include drive like 'C:/...'; file URI needs a third slash
        uri = f"file:///{abs_path.as_posix()}"
        st = await asyncio.to_thread(abs_path.stat)
        ctype, _ = mimetypes.guess_type(str(abs_path))
        return FileInfo(
            uri=uri,
            size=st.st_size,
            content_type=ctype,
            etag=None,
            modified_at=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
        )

    def _path_from_file_uri(self, uri: str) -> Path:
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            raise FileServiceError(
                f"Invalid file URI scheme for LocalDirectoryFileService: {uri!r}"
            )

        # Only local host allowed
        if parsed.netloc not in ("", "localhost"):
            raise FileServiceError(f"Non-local file URI not supported: {uri!r}")

        raw_path = unquote(parsed.path)

        # Windows: urlparse on file:///C:/path -> path "/C:/path"
        # POSIX:   "/var/data/path"
        path = Path(raw_path)

        # Normalize/resolve to absolute path
        try:
            path = path.resolve()
        except Exception as e:
            raise FileServiceError(
                f"Unable to resolve path from URI {uri!r}: {e}"
            ) from e

        # Sandbox check
        if self._settings.root and not self._settings.allow_outside_root:
            root = self._settings.root
            try:
                path.relative_to(root)
            except ValueError:
                raise FileServiceError(
                    f"Access outside sandbox root is not allowed: {path} (root={root})"
                )

        return path

    async def _ensure_exists_file(self, path: Path, uri: str) -> None:
        def _check():
            if not path.exists():
                raise NotFoundError(f"Object not found: {uri}")
            if not path.is_file():
                raise FileServiceError(f"Not a file: {uri}")

        await asyncio.to_thread(_check)
