from src.base.domain.dto import BaseDTO
from src.users.domain.enums.user_type import UserType


class UserDTO(BaseDTO):
    __serialize_exclude__ = {"password"}

    def __init__(
        self,
        id: int,
        username: str,
        first_name: str,
        sur_name: str,
        phone_number: str,
        user_type: UserType = UserType.user,
    ):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.sur_name = sur_name
        self.phone_number = phone_number
        self.user_type = user_type
        self.password = ""  # Placeholder, excluded from serialization
