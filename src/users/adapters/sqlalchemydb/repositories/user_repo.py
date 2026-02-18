from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.base.ports.repositories.cache_repository import AbstractCacheRepository
from src.users.adapters.sqlalchemydb.models.user import UserModel
from src.users.adapters.sqlalchemydb.models.base_user import BaseUserModel
from src.users.domain.enums.user_type import UserType
from src.users.domain.entities.user import User
from src.users.ports.repositories.user_repo_port import UserRepositoryPort


class SqlalchemyUserRepository(
    AsyncSqlalchemyRepository[User, UserModel],
    UserRepositoryPort,
):

    def __init__(
        self,
        session: AsyncSession,
        cache_repo: Optional[AbstractCacheRepository] = None,
    ) -> None:
        super().__init__(session, UserModel, cache_repo=cache_repo)

    async def get_by_username(
        self,
        *,
        username: str,
        include_deleted: bool = False,
        use_cache: bool = True,
        ttl: int | None = None,
        **kwargs,
    ) -> User | None:
        # Check cache if enabled
        if self._cache and use_cache:
            cache_key = f"{self.model.__name__}:username:{username}"
            cached = await self._cache.get(key=cache_key)
            if cached is not None:
                return cached

        # Query database
        stmt = (
            select(UserModel)
            .join(BaseUserModel, UserModel.id == BaseUserModel.id)
            .where(BaseUserModel.username == username)
            .where(BaseUserModel.user_type == UserType.user)
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
