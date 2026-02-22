from sqlalchemy import select
from sqlalchemy.orm import aliased

from src.base.adapters.sqlalchemydb.queries import AsyncSqlalchemyQueries
from src.messaging.ports.queries.messaging_queries_port import MessagingQueriesPort

from src.messaging.adapters.sqlalchemydb.models.message import MessageModel
from src.messaging.adapters.sqlalchemydb.models.messaging_request import (
    MessagingRequestModel,
)

from src.messaging.domain.dtos.message_dto import MessageDTO
from src.messaging.domain.dtos.messaging_request_dto import MessageRequestDTO

from src.users.adapters.sqlalchemydb.models.base_user import BaseUserModel
from src.users.domain.dtos.user_dto import UserDTO

from src.files.adapters.sqlalchemydb.models.file import FileModel
from src.files.domain.dtos.file_dto import FileDTO


class SqlalchemyMessagingQueries(AsyncSqlalchemyQueries, MessagingQueriesPort):
    # -----------------------------------------------------------------
    # DTO Mappers
    # -----------------------------------------------------------------

    def _to_message_dto(self, m: MessageModel) -> MessageDTO:
        return MessageDTO(
            id=m.id,
            message_request_id=m.message_request_id,
            text=m.text,
            phone_number=m.phone_number,
            username=m.username,
            user_id=m.user_id,
            attachment_file_id=m.attachment_file_id,
            sending_time=m.sending_time,
            sent_time=m.sent_time,
            status=m.status,
            error_message=m.error_message,
        )

    def _map_request_row_to_dto(self, row: tuple) -> MessageRequestDTO:
        request_model, user_model, csv_file_row, attachment_file_row = row

        # Convert related models to DTOs (may be None due to LEFT JOIN)
        user_dto = self._to_user_dto(user_model) if user_model else None
        csv_file_dto = (
            FileDTO(
                id=csv_file_row.id,
                uri=csv_file_row.uri,
                name=csv_file_row.name,
                size=csv_file_row.size,
                content_type=csv_file_row.content_type,
                etag=csv_file_row.etag,
                created_at=csv_file_row.created_at,
                modified_at=csv_file_row.modified_at,
                meta=csv_file_row.meta,
            )
            if csv_file_row
            else None
        )
        attachment_file_dto = (
            FileDTO(
                id=attachment_file_row.id,
                uri=attachment_file_row.uri,
                name=attachment_file_row.name,
                size=attachment_file_row.size,
                content_type=attachment_file_row.content_type,
                etag=attachment_file_row.etag,
                created_at=attachment_file_row.created_at,
                modified_at=attachment_file_row.modified_at,
                meta=attachment_file_row.meta,
            )
            if attachment_file_row
            else None
        )

        return MessageRequestDTO(
            id=request_model.id,
            user=user_dto,
            session_id=request_model.session_id,
            csv_file=csv_file_dto,
            attachment_file=attachment_file_dto,
            title=request_model.title,
            default_text=request_model.default_text,
            sending_time=request_model.sending_time,
        )

    def _to_user_dto(self, u: BaseUserModel) -> UserDTO:
        return UserDTO(
            id=u.id,
            username=u.username,
            first_name=u.first_name,
            sur_name=u.sur_name,
            phone_number=u.phone_number,
            user_type=u.user_type,
        )

    def _to_file_dto(self, f: FileModel) -> FileDTO:
        return FileDTO(
            id=f.id,
            uri=f.uri,
            name=f.name,
            size=f.size,
            content_type=f.content_type,
            etag=f.etag,
            created_at=f.created_at,
            modified_at=f.modified_at,
            meta=f.meta,
        )

    # -----------------------------------------------------------------
    # Query Implementations
    # -----------------------------------------------------------------

    async def get_request_details(self, *, request_id: int) -> MessageRequestDTO | None:
        # Use aliased ORM models for joining the same File table twice
        CsvFile = aliased(FileModel, name="csv_file")
        AttachmentFile = aliased(FileModel, name="attachment_file")

        # Build a single query with all joins
        stmt = (
            select(
                MessagingRequestModel,
                BaseUserModel,
                CsvFile,
                AttachmentFile,
            )
            .select_from(MessagingRequestModel)
            .outerjoin(
                BaseUserModel,
                (BaseUserModel.id == MessagingRequestModel.user_id)
                & (BaseUserModel.deleted_at.is_(None)),
            )
            .outerjoin(
                CsvFile,
                (CsvFile.id == MessagingRequestModel.request_file_id)
                & (CsvFile.deleted_at.is_(None)),
            )
            .outerjoin(
                AttachmentFile,
                (AttachmentFile.id == MessagingRequestModel.attachment_file_id)
                & (AttachmentFile.deleted_at.is_(None)),
            )
            .where(
                MessagingRequestModel.id == request_id,
                MessagingRequestModel.deleted_at.is_(None),
            )
        )

        return await self._one_tuple(stmt, self._map_request_row_to_dto)

    async def get_messages_for_request(self, *, request_id: int) -> list[MessageDTO]:
        stmt = (
            select(MessageModel)
            .where(
                MessageModel.message_request_id == request_id,
                MessageModel.deleted_at.is_(None),
            )
            .order_by(MessageModel.sending_time.asc())
        )

        return await self._all(stmt, self._to_message_dto)
