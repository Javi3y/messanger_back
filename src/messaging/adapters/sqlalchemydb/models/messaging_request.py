from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from src.base.adapters.sqlalchemydb.database import Base
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.messaging.domain.entities.messaging_request import MessagingRequest


class MessagingRequestModel(Base, EntityModelMixin):
    __tablename__ = "messaging_requests"

    # entity mapping
    entity_cls = MessagingRequest
    _entity_fields = [
        "user_id",
        "title",
        "session_id",
        "request_file_id",
        "attachment_file_id",
        "sending_time",
        "generated",
        "default_text",
    ]

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id = Column(
        Integer,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    request_file_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    attachment_file_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = Column(String(255), nullable=True)

    sending_time = Column(DateTime(timezone=True), nullable=False)

    generated = Column(Boolean, nullable=False, default=False)

    default_text = Column(Text, nullable=True)

    deleted_at = Column(DateTime(timezone=True), nullable=True)
