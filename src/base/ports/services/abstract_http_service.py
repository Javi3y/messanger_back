from types import TracebackType
from src.base.ports.services.abstract_http_client import AbstractAsyncHttpClient
from src.base.ports.services.service import AsyncAbstractService


class AbstractAsyncHttpService(AsyncAbstractService):
    client: "AbstractAsyncHttpClient"

    async def __aenter__(self):
        """Enter async context, ensuring the client is also entered."""
        client = await self.client.__aenter__()
        self.client: "AbstractAsyncHttpClient" = client
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ):
        """Exit async context, ensuring the client is also exited."""
        await self.client.__aexit__(
            exc_type,
            exc_val,
            exc_tb,
        )
        return self
