from sqlalchemy import Column, DateTime, Integer, String, Enum
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.base.adapters.sqlalchemydb.database import Base
from src.users.domain.enums.user_type import UserType
from src.users.domain.entities.base_user import BaseUser


class BaseUserModel(Base, EntityModelMixin):
    __tablename__ = "base_users"
    entity_cls = BaseUser
    _entity_fields = [
        "username",
        "password",
        "first_name",
        "sur_name",
        "phone_number",
        "user_type",
    ]

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    sur_name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": UserType.base_user,
        "polymorphic_on": user_type,
    }
