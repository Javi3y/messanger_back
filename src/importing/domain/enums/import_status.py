from src.base.domain.enum import BaseStrEnum


class ImportStatus(BaseStrEnum):
    pending = "pending"
    staging = "staging"
    staged = "staged"
    processing = "processing"
    completed = "completed"
    failed = "failed"
