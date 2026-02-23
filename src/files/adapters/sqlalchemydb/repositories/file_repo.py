from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.base.adapters.sqlalchemydb.repository import AsyncSqlalchemyRepository
from src.files.adapters.sqlalchemydb.models.file import FileModel
from src.files.domain.entities.file import File
from src.files.ports.repositories.file_repo_port import FileRepositoryPort


class SqlalchemyFileRepository(
    AsyncSqlalchemyRepository[File, FileModel],
    FileRepositoryPort,
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FileModel)

    # --- lookups -------------------------------------------------------------

    async def get_by_uri(
        self,
        *,
        uri: str,
        include_deleted: bool = False,
        **kwargs,
    ) -> File | None:
        stmt = select(FileModel).where(FileModel.uri == uri)
        if not include_deleted:
            stmt = stmt.where(FileModel.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None

    async def find_by_etag(
        self,
        *,
        etag: str,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[File]:
        stmt = (
            select(FileModel).where(FileModel.etag == etag).offset(offset).limit(limit)
        )

        if not include_deleted:
            stmt = stmt.where(FileModel.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]

    async def search_by_name(
        self,
        *,
        name_like: str,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
        **kwargs,
    ) -> list[File]:
        stmt = (
            select(FileModel)
            .where(FileModel.name.ilike(f"%{name_like}%"))
            .offset(offset)
            .limit(limit)
        )
        if not include_deleted:
            stmt = stmt.where(FileModel.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]

    async def list_visible_for_user(
        self,
        *,
        user_id: int,
        include_public: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[File]:
        visibility_clause = (
            or_(FileModel.user_id == user_id, FileModel.user_id.is_(None))
            if include_public
            else FileModel.user_id == user_id
        )

        stmt = (
            select(FileModel)
            .where(FileModel.deleted_at.is_(None), visibility_clause)
            .order_by(FileModel.id.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]
