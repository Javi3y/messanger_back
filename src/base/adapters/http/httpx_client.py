from typing import Literal
from httpx import AsyncClient

from src.base.ports.services.abstract_http_client import AbstractAsyncHttpClient


class HttpxAsyncClient(AbstractAsyncHttpClient[AsyncClient]):
    def __init__(self, base_url: str, timeout: int = 10):
        super().__init__(base_url)
        self._client = AsyncClient(
            base_url=base_url,
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _request(
        self,
        method: Literal["POST", "GET", "PUT", "DELETE", "PATCH"],
        path: str,
        headers: dict | None,
        params: dict | None = None,
        json_data: dict | None = None,
        data: dict | None = None,
    ) -> dict | None:

        response = await self._client.request(
            method=method,
            url=path,
            headers=headers,
            params=params,
            json=json_data,
            data=data,
        )
        response.raise_for_status()
        return response.json() if response.status_code != 204 else None
