from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, text
from sqlalchemy.sql import func

from src.base.adapters.sqlalchemydb.database import Base
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.base.domain.entities.outbox_event import OutboxEvent


class OutboxEventModel(Base, EntityModelMixin):
    __tablename__ = "outbox_events"

    entity_cls = OutboxEvent
    _entity_fields = [
        "event_type",
        "payload",
        "available_at",
        "processed_at",
        "attempts",
        "last_error",
        "dedup_key",
        "aggregate_type",
        "aggregate_id",
        "created_at",
    ]

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String(200), nullable=False, index=True)
    payload = Column(JSON, nullable=False)

    available_at = Column(
        DateTime(timezone=True), nullable=False, index=True, server_default=func.now()
    )
    processed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    attempts = Column(Integer, nullable=False, server_default=text("0"))
    last_error = Column(Text, nullable=True)

    dedup_key = Column(String(255), nullable=True, index=True)
    aggregate_type = Column(String(50), nullable=True, index=True)
    aggregate_id = Column(String(128), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, index=True, server_default=func.now()
    )
