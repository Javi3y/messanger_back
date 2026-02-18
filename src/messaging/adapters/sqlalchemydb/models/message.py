from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from src.base.adapters.sqlalchemydb.database import Base
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.messaging.domain.entities.message import Message
from src.messaging.domain.enums.message_status import MessageStatus


class MessageModel(Base, EntityModelMixin):
    __tablename__ = "messages"

    # entity mapping
    entity_cls = Message
    _entity_fields = [
        "message_request_id",
        "sending_time",
        "sent_time",
        "text",
        "phone_number",
        "username",
        "user_id",
        "attachment_file_id",
        "status",
        "error_message",
    ]

    id = Column(Integer, primary_key=True, index=True)

    message_request_id = Column(
        Integer,
        ForeignKey("messaging_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sending_time = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    sent_time = Column(DateTime(timezone=True), nullable=True)

    text = Column(Text, nullable=False)

    phone_number = Column(String(50), nullable=True, index=True)
    username = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)

    attachment_file_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(
        Enum(MessageStatus, name="message_status"),
        nullable=False,
        default=MessageStatus.pending,
    )

    error_message = Column(Text, nullable=True)

    deleted_at = Column(DateTime(timezone=True), nullable=True)
