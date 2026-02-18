from typing import Generic, Type, TypeVar
from hashlib import sha256
from json import dumps
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.base.ports.repositories.repository import AbstractRepository
from src.base.domain.entity import BaseEntity
from src.base.ports.repositories.cache_repository import AbstractCacheRepository

E = TypeVar("E", bound=BaseEntity)
M = TypeVar("M", bound=EntityModelMixin)


class AsyncSqlalchemyRepository(AbstractRepository, Generic[E, M]):

    def __init__(
        self,
        session: AsyncSession,
        model: Type[M],
        cache_repo: AbstractCacheRepository | None = None,
        *,
        default_ttl: int = 3600,
    ) -> None:
        super().__init__(session)
        self.session: AsyncSession = session
        self.model: Type[M] = model
        self._cache = cache_repo
        self._default_ttl = default_ttl

    # -------------------------
    # Write operations
    # -------------------------

    async def add(
        self,
        *,
        entity: E,
        **kwargs,
    ) -> E:
        model = self.model.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def update(
        self,
        *,
        entity: E,
        **kwargs,
    ) -> E:
        model = self.model.from_entity(entity)
        merged: M = await self.session.merge(model)  # type: ignore[assignment]
        await self.session.flush()
        await self.session.refresh(merged)
        result = merged.to_entity()

        if self._cache and entity.id is not None:
            await self._invalidate_model_caches()

        return result

    async def delete(
        self,
        *,
        id: int,
        soft_delete: bool = True,
        **kwargs,
    ) -> None:
        model = await self.session.get(self.model, id)
        if not model:
            return

        if self._cache:
            await self._invalidate_model_caches()

        if soft_delete and hasattr(model, "deleted_at"):
            from datetime import datetime, timezone

            setattr(model, "deleted_at", datetime.now(timezone.utc))
            await self.session.flush()
        else:
            await self.session.delete(model)
            await self.session.flush()

    # -------------------------
    # Cache helpers
    # -------------------------

    def _id_cache_key(self, id: int) -> str:
        """Generate cache key for entity by ID."""
        return f"{self.model.__name__}:id:{id}"

    def _query_cache_key(self, **params) -> str:
        param_str = dumps(sorted(params.items()), sort_keys=True, default=str)
        hash_hex = sha256(param_str.encode()).hexdigest()[:16]
        return f"{self.model.__name__}:query:{hash_hex}"

    async def _invalidate_model_caches(self) -> None:
        if not self._cache:
            return
        await self._cache.clear(prefix=f"{self.model.__name__}:")

    # -------------------------
    # Read operations
    # -------------------------

    async def get(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
        use_cache: bool = True,
        ttl: int | None = None,
        **kwargs,
    ) -> list[E]:
        # Check cache if enabled
        if self._cache and use_cache:
            cache_key = self._query_cache_key(
                limit=limit, offset=offset, include_deleted=include_deleted, **kwargs
            )
            cached = await self._cache.get(key=cache_key)
            if cached is not None:
                return cached

        # Query database
        stmt = select(self.model).offset(offset).limit(limit)
        if not include_deleted:
            if hasattr(self.model, "deleted_at"):
                stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        entities = [m.to_entity() for m in models]

        # Store in cache if enabled
        if self._cache and use_cache:
            cache_key = self._query_cache_key(
                limit=limit, offset=offset, include_deleted=include_deleted, **kwargs
            )
            await self._cache.set(
                key=cache_key, value=entities, ttl=ttl or self._default_ttl
            )

        return entities

    async def get_by_id(
        self,
        *,
        id: int,
        include_deleted: bool = False,
        use_cache: bool = True,
        ttl: int | None = None,
        **kwargs,
    ) -> E | None:
        # Check cache if enabled
        if self._cache and use_cache:
            cache_key = self._id_cache_key(id)
            cached = await self._cache.get(key=cache_key)
            if cached is not None:
                return cached

        # Query database
        model = await self.session.get(self.model, id)
        if not model:
            return None
        if not include_deleted:
            if hasattr(self.model, "deleted_at") and getattr(model, "deleted_at", None):
                return None
        entity = model.to_entity()

        # Store in cache if enabled
        if self._cache and use_cache and entity is not None:
            cache_key = self._id_cache_key(id)
            await self._cache.set(
                key=cache_key, value=entity, ttl=ttl or self._default_ttl
            )

        return entity
