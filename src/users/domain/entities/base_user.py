from datetime import datetime
from src.base.domain.entity import BaseEntity
from src.users.domain.enums.user_type import UserType


class BaseUser(BaseEntity):
    repo_attr = "base_user_repo"
    __serialize_exclude__ = {"password"}
    username: str
    password: str
    first_name: str
    sur_name: str
    phone_number: str
    user_type: UserType = UserType.user

    def __init__(
        self,
        username: str,
        password: str,
        first_name: str,
        sur_name: str,
        phone_number: str,
        id: int | None = None,
        user_type: UserType = UserType.base_user,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id, deleted_at=deleted_at)
        self.username = username
        self.first_name = first_name
        self.sur_name = sur_name
        self.password = password
        self.phone_number = phone_number
        self.user_type = user_type
