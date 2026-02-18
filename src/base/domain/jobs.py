from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True, slots=True)
class JobSpec:
    job: Callable[..., Awaitable[dict[str, int]]]
    interval: float
    batch: int
