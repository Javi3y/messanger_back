# ensure decorator registration happens when imported
from src.messaging.application.import_handlers.message_request_import_handler import (  # noqa: F401
    MessageRequestImportHandler,
)
