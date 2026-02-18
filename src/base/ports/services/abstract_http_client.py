from abc import abstractmethod
from types import TracebackType
from typing import Generic, Literal, TypeVar

from src.base.ports.services.client import AbstractClient

ClientT = TypeVar("ClientT")


class AbstractAsyncHttpClient(AbstractClient, Generic[ClientT]):
    base_url: str
    _client: ClientT

    def __init__(self, base_url: str):
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url

    async def __aenter__(self) -> "AbstractAsyncHttpClient":
        await self._client.__aenter__()
        return self

    @abstractmethod
    async def _request(
        self,
        method: Literal["POST", "GET", "PUT", "DELETE", "PATCH"],
        path: str,
        headers: dict | None,
        params: dict | None = None,
        json_data: dict | None = None,
        data: dict | None = None,
    ) -> dict | None:
        pass

    async def request(
        self,
        method: Literal["POST", "GET", "PUT", "DELETE", "PATCH"],
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
        json_data: dict | None = None,
        data: dict | None = None,
    ) -> dict | None:
        return await self._request(
            method=method,
            path=path,
            headers=headers,
            params=params,
            json_data=json_data,
            data=data,
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_val, exc_tb)
