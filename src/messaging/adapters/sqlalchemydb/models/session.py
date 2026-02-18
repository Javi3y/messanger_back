from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.base.adapters.sqlalchemydb.database import Base
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.messaging.domain.entities.session import Session, MessengerType


class SessionModel(Base, EntityModelMixin):
    __tablename__ = "sessions"

    # entity mapping
    entity_cls = Session
    _entity_fields = [
        "id",
        "deleted_at",
        "user_id",
        "title",
        "phone_number",
        "session_type",
        "session_str",
        "uuid",
        "is_active",
    ]

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(50), nullable=False)
    phone_number = Column(String(50), nullable=False, index=True)

    # same enum pattern as UserType
    session_type = Column(
        Enum(MessengerType, name="messenger_type"),
        nullable=False,
    )

    session_str = Column(String, nullable=True)

    uuid = Column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=True,
        index=True,
    )

    is_active = Column(Boolean, nullable=False, default=False)

    deleted_at = Column(DateTime(timezone=True), nullable=True)
