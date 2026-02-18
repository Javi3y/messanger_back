# Import handler modules so @outbox_handler decorators register them
from src.importing.application.outbox_handlers import (
    bulk_import_process,
    bulk_import_stage,
)  # noqa: F401
