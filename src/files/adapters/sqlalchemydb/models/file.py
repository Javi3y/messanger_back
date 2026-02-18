from sqlalchemy import Column, Integer, String, DateTime, BigInteger, JSON, Index
from src.base.adapters.sqlalchemydb.database import Base
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.files.domain.entities.file import File


class FileModel(Base, EntityModelMixin):
    __tablename__ = "files"

    entity_cls = File
    _entity_fields = [
        "uri",
        "name",
        "size",
        "content_type",
        "etag",
        "created_at",
        "modified_at",
        "meta",
    ]

    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String(2048), nullable=False, unique=True)
    name = Column(String(512), nullable=False)
    size = Column(BigInteger, nullable=True)
    content_type = Column(String(255), nullable=True)
    etag = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    meta = Column(JSON, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_files_uri", "uri", unique=True),
        Index("ix_files_etag", "etag"),
        Index("ix_files_name", "name"),
    )
