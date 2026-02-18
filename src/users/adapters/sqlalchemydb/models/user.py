from sqlalchemy import Boolean, Column, Integer, ForeignKey

from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.users.adapters.sqlalchemydb.models.base_user import BaseUserModel
from src.users.domain.enums.user_type import UserType
from src.users.domain.entities.user import User


class UserModel(BaseUserModel, EntityModelMixin):
    __tablename__ = "users"

    id = Column(Integer, ForeignKey("base_users.id"), primary_key=True)

    # extra fields for User
    is_active = Column(Boolean, nullable=False, default=False)

    entity_cls = User
    _entity_fields = [
        "username",
        "password",
        "first_name",
        "sur_name",
        "phone_number",
        "is_active",
    ]

    __mapper_args__ = {
        "polymorphic_identity": UserType.user,
    }
