from typing import Any, Awaitable, Callable, Generic, TypeVar

from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.base.domain.entity import BaseEntity
from src.base.ports.unit_of_work import AsyncUnitOfWork

E = TypeVar("E", bound=BaseEntity)
Loader = Callable[[AsyncUnitOfWork], Awaitable[E | None]]


class LazyEntityCache(Generic[E]):
    def __init__(
        self,
        cache_repo: AbstractCacheRepository,
        *,
        key_prefix: str = "entity",
        default_ttl: int | None = None,
        uow: AsyncUnitOfWork | None = None,
    ) -> None:
        self._cache = cache_repo
        self._prefix = key_prefix.rstrip(":")
        self._default_ttl = default_ttl
        self._uow: AsyncUnitOfWork | None = uow

    def set_uow(self, uow: AsyncUnitOfWork) -> "LazyEntityCache":
        self._uow = uow
        return self

    def _require_uow(self) -> AsyncUnitOfWork:
        if self._uow is None:
            raise RuntimeError(
                "AsyncUnitOfWork is not set on LazyEntityCache. "
                "Call lazy_cache.set_uow(uow) before using it, "
                "or inject a UoW via the container."
            )
        return self._uow

    # -------------------------
    # Helpers
    # -------------------------

    def _cache_key(self, entity_type: type[E], identifier: Any) -> str:
        if self._prefix:
            return f"{self._prefix}:{entity_type.__name__}:{identifier}"
        return f"{entity_type.__name__}:{identifier}"

    def _get_repo_from_uow(self, uow: AsyncUnitOfWork, entity_type: type[E]) -> Any:
        repo_attr = getattr(entity_type, "repo_attr", None)
        if not repo_attr:
            raise RuntimeError(
                f"{entity_type.__name__} does not define 'repo_attr', "
                "so LazyEntityCache cannot resolve its repository."
            )

        try:
            return getattr(uow, repo_attr)
        except AttributeError as exc:
            raise RuntimeError(
                f"UnitOfWork has no attribute '{repo_attr}' "
                f"for entity {entity_type.__name__}"
            ) from exc

    # -------------------------
    # Generic get-or-load (no uow param anymore)
    # -------------------------

    async def get_or_load(
        self,
        *,
        key: str,
        loader: Loader,
        ttl: int | None = None,
    ) -> E | None:
        uow = self._require_uow()

        cached = await self._cache.get(key=key)
        if cached is not None:
            return cached

        entity = await loader(uow)

        if entity is not None:
            await self._cache.set(
                key=key,
                value=entity,
                ttl=ttl if ttl is not None else self._default_ttl,
            )

        return entity

    # -------------------------
    # Public: get by id (no uow argument)
    # -------------------------

    async def get_by_id(
        self,
        *,
        entity_type: type[E],
        id: Any,
        ttl: int | None = None,
    ) -> E | None:
        uow = self._require_uow()
        key = self._cache_key(entity_type, id)
        repo = self._get_repo_from_uow(uow, entity_type)

        async def loader(_: AsyncUnitOfWork) -> E | None:
            # we ignore the parameter and capture `repo` from outside
            return await repo.get_by_id(id=id)  # type: ignore[no-any-return]

        return await self.get_or_load(
            key=key,
            loader=loader,
            ttl=ttl,
        )
