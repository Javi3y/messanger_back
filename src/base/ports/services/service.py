from abc import ABC, abstractmethod

from src.base.ports.services.client import AbstractClient


class AsyncAbstractService(ABC):
    def __init__(self, client: AbstractClient):
        self.client = client

    @abstractmethod
    async def authenticate(self, **kwargs):
        raise NotImplementedError
