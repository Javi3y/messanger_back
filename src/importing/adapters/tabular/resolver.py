from src.importing.ports.services.tabular_reader_port import (
    TabularDocument,
    TabularReaderPort,
)


class TabularReaderResolver(TabularReaderPort):
    def __init__(self, readers: list[TabularReaderPort]) -> None:
        self._readers = readers

    def can_read(self, *, filename: str | None, content_type: str | None) -> bool:
        return any(
            r.can_read(filename=filename, content_type=content_type)
            for r in self._readers
        )

    def read(
        self, *, filename: str | None, content_type: str | None, content: bytes
    ) -> TabularDocument:
        for r in self._readers:
            if r.can_read(filename=filename, content_type=content_type):
                return r.read(
                    filename=filename, content_type=content_type, content=content
                )
        # default: empty doc (outbox handler will mark job failed)
        return TabularDocument(headers=[], rows=[])
