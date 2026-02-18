import csv
import io
from typing import Any

from src.importing.ports.services.tabular_reader_port import (
    TabularDocument,
    TabularReaderPort,
    TabularRow,
)


def _decode_csv_bytes(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1256", "windows-1256", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


class CsvTabularReader(TabularReaderPort):
    def can_read(self, *, filename: str | None, content_type: str | None) -> bool:
        name = (filename or "").lower()
        ct = (content_type or "").lower()
        return name.endswith(".csv") or "text/csv" in ct or "application/csv" in ct

    def read(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        content: bytes,
    ) -> TabularDocument:
        text = _decode_csv_bytes(content)
        buf = io.StringIO(text, newline="")
        reader = csv.DictReader(buf)

        headers = [h.strip() for h in (reader.fieldnames or []) if h and h.strip()]
        if not headers:
            return TabularDocument(headers=[], rows=[])

        def _iter_rows():
            # CSV header is row 1 => first data row is 2
            row_number = 2
            for row in reader:
                if row is None:
                    row_number += 1
                    continue
                cleaned: dict[str, Any] = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    cleaned[k.strip()] = v
                yield TabularRow(row_number=row_number, values=cleaned)
                row_number += 1

        return TabularDocument(headers=headers, rows=_iter_rows())
