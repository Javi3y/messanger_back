from typing import Callable, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

from src.base.ports.queries.queries import QueryParams

T = TypeVar("T")


class AsyncSqlalchemyQueries:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _apply_params(self, stmt, params: QueryParams | None):
        if not params:
            return stmt
        return stmt.offset(params.offset).limit(params.limit)

    async def _all(self, stmt: Executable, mapper: Callable[[object], T]) -> list[T]:
        res = await self.session.execute(stmt)
        return [mapper(row) for row in res.scalars().all()]

    async def _one(self, stmt: Executable, mapper: Callable[[object], T]) -> T | None:
        res = await self.session.execute(stmt)
        model = res.scalars().first()
        return None if model is None else mapper(model)

    async def _one_tuple(
        self,
        stmt: Executable,
        mapper: Callable[[tuple], T],
    ) -> T | None:
        res = await self.session.execute(stmt)
        row = res.first()
        return None if row is None else mapper(tuple(row))
