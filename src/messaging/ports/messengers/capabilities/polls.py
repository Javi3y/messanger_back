from abc import ABC, abstractmethod
from typing import Sequence

from src.messaging.domain.entities.contact import Contact


class PollsPort(ABC):

    @abstractmethod
    async def send_poll(
        self,
        *,
        contact: Contact,
        question: str,
        options: Sequence[str],
        allows_multiple_answers: bool = False,
        is_anonymous: bool = True,
    ) -> None:
        raise NotImplementedError
