from sqlalchemy import or_, select

from src.base.adapters.sqlalchemydb.queries import AsyncSqlalchemyQueries
from src.files.adapters.sqlalchemydb.models.file import FileModel
from src.files.domain.dtos.file_dto import FileDTO
from src.files.ports.queries.file_queries_port import FileQueriesPort
from src.users.adapters.sqlalchemydb.models.base_user import BaseUserModel
from src.users.domain.dtos.user_dto import UserDTO


class SqlalchemyFileQueries(AsyncSqlalchemyQueries, FileQueriesPort):
    @staticmethod
    def _to_file_dto(row: tuple[FileModel, BaseUserModel | None]) -> FileDTO:
        file_row, user_row = row
        return FileDTO(
            id=file_row.id,
            uri=file_row.uri,
            name=file_row.name,
            size=file_row.size,
            content_type=file_row.content_type,
            etag=file_row.etag,
            created_at=file_row.created_at,
            modified_at=file_row.modified_at,
            meta=file_row.meta,
            owner_id=file_row.user_id,
            user=(
                None
                if user_row is None
                else UserDTO(
                    id=user_row.id,
                    username=user_row.username,
                    first_name=user_row.first_name,
                    sur_name=user_row.sur_name,
                    phone_number=user_row.phone_number,
                    user_type=user_row.user_type,
                )
            ),
            is_public=file_row.user_id is None,
        )

    async def get_file_with_owner(self, *, file_id: int) -> FileDTO | None:
        stmt = (
            select(FileModel, BaseUserModel)
            .select_from(FileModel)
            .outerjoin(
                BaseUserModel,
                (BaseUserModel.id == FileModel.user_id)
                & (BaseUserModel.deleted_at.is_(None)),
            )
            .where(FileModel.id == file_id, FileModel.deleted_at.is_(None))
        )
        return await self._one_tuple(stmt, self._to_file_dto)

    async def list_files_with_owner(
        self,
        *,
        user_id: int,
        include_public: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FileDTO]:
        visibility_clause = (
            or_(FileModel.user_id == user_id, FileModel.user_id.is_(None))
            if include_public
            else FileModel.user_id == user_id
        )
        stmt = (
            select(FileModel, BaseUserModel)
            .select_from(FileModel)
            .outerjoin(
                BaseUserModel,
                (BaseUserModel.id == FileModel.user_id)
                & (BaseUserModel.deleted_at.is_(None)),
            )
            .where(FileModel.deleted_at.is_(None), visibility_clause)
            .order_by(FileModel.id.desc())
            .offset(offset)
            .limit(limit)
        )

        res = await self.session.execute(stmt)
        rows = res.all()
        return [self._to_file_dto((row[0], row[1])) for row in rows]
