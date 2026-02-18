from src.base.domain.enum import BaseStrEnum


class MessageStatus(BaseStrEnum):
    pending = "PENDING"
    failed = "FAILED"
    successful = "SUCCESSFUL"
