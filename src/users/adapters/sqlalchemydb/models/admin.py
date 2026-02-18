from sqlalchemy import Column, Integer, ForeignKey
from src.base.adapters.sqlalchemydb.mixins import EntityModelMixin
from src.users.adapters.sqlalchemydb.models.base_user import BaseUserModel
from src.users.domain.entities.admin import Admin
from src.users.domain.enums.user_type import UserType


class AdminModel(BaseUserModel, EntityModelMixin):
    __tablename__ = "admins"

    id = Column(Integer, ForeignKey("base_users.id"), primary_key=True)
    entity_cls = Admin
    _entity_fields = [
        "username",
        "password",
        "first_name",
        "sur_name",
        "phone_number",
    ]

    __mapper_args__ = {
        "polymorphic_identity": UserType.admin,
    }
