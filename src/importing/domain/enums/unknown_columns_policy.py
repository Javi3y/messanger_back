from src.base.domain.enum import BaseStrEnum


class UnknownColumnsPolicy(BaseStrEnum):
    error = "error"  # unknown header => fail
    ignore = "ignore"  # unknown header => ignore
    capture = "capture"  # unknown header => store into extras (key=header)
