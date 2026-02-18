from src.importing.domain.dtos.base_import_config import BaseImportConfig
from src.importing.ports.import_handler_port import ImportHandlerPort
from src.messaging.application.import_handlers.message_request_import_config import (
    MessageRequestImportConfig,
)
from src.messaging.application.import_handlers.message_request_import_handler import (
    MessageRequestImportHandler,
)


class ImportRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, type[ImportHandlerPort]] = {}
        self._configs: dict[str, type[BaseImportConfig]] = {}
        self.register(
            import_type="message_request",
            config_cls=MessageRequestImportConfig,
            handler_cls=MessageRequestImportHandler,
        )

    def register(
        self,
        *,
        import_type: str,
        config_cls: type[BaseImportConfig],
        handler_cls: type[ImportHandlerPort],
    ) -> None:
        self._handlers[import_type] = handler_cls
        self._configs[import_type] = config_cls

    def get_handler(self, *, import_type: str) -> type[ImportHandlerPort] | None:
        return self._handlers.get(import_type)

    def get_config(self, *, import_type: str) -> type[BaseImportConfig] | None:
        return self._configs.get(import_type)

    def is_registered(self, *, import_type: str) -> bool:
        return import_type in self._handlers
