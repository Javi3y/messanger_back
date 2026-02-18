from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.users.adapters.sqlalchemydb.models.admin import AdminModel
from src.users.adapters.sqlalchemydb.models.user import UserModel
from src.users.adapters.sqlalchemydb.models.base_user import BaseUserModel
from src.users.domain.entities.base_user import BaseUser
from src.users.domain.enums.user_type import UserType
from src.users.ports.repositories.base_user_repo_port import (
    BaseUserRepositoryPort,
)


class SqlalchemyBaseUserRepository(
    AsyncSqlalchemyRepository[BaseUser, BaseUserModel],
    BaseUserRepositoryPort,
):

    def __init__(
        self,
        session: AsyncSession,
        cache_repo: Optional[AbstractCacheRepository] = None,
    ) -> None:
        super().__init__(session, BaseUserModel, cache_repo=cache_repo)

    async def get_by_username(
        self,
        *,
        username: str,
        include_deleted: bool = False,
        use_cache: bool = True,
        ttl: int | None = None,
        **kwargs,
    ) -> BaseUser | None:
        if self._cache and use_cache:
            cache_key = f"{self.model.__name__}:username:{username}"
            cached = await self._cache.get(key=cache_key)
            if cached is not None:
                return cached

        stmt = (
            select(BaseUserModel)
            .where(BaseUserModel.username == username)
            .options(selectin_polymorphic(BaseUserModel, [AdminModel, UserModel]))
        )
        if not include_deleted:
            stmt = stmt.where(BaseUserModel.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        entity = model.to_entity() if model else None

        # Store in cache if enabled
        if self._cache and use_cache and entity is not None:
            cache_key = f"{self.model.__name__}:username:{username}"
            await self._cache.set(
                key=cache_key, value=entity, ttl=ttl or self._default_ttl
            )

        return entity

    async def list_by_type(
        self,
        *,
        user_type: UserType,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
        use_cache: bool = True,
        ttl: int | None = None,
        **kwargs,
    ) -> Sequence[BaseUser]:
        # Check cache if enabled
        if self._cache and use_cache:
            cache_key = f"{self.model.__name__}:type:{user_type.value}:{limit}:{offset}:{include_deleted}"
            cached = await self._cache.get(key=cache_key)
            if cached is not None:
                return cached

        stmt = (
            select(BaseUserModel)
            .where(BaseUserModel.user_type == user_type)
            .where(BaseUserModel.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        if not include_deleted:
            stmt = stmt.where(BaseUserModel.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        entities = [m.to_entity() for m in res.scalars().all()]

        if self._cache and use_cache:
            cache_key = f"{self.model.__name__}:type:{user_type.value}:{limit}:{offset}:{include_deleted}"
            await self._cache.set(
                key=cache_key, value=entities, ttl=ttl or self._default_ttl
            )

        return entities
