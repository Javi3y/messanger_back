from datetime import datetime
from src.users.domain.enums.user_type import UserType
from src.users.domain.entities.base_user import BaseUser


class User(BaseUser):
    repo_attr = "user_repo"
    is_active: bool = False

    def __init__(
        self,
        username: str,
        password: str,
        first_name: str,
        sur_name: str,
        phone_number: str,
        id: int | None = None,
        deleted_at: datetime | None = None,
        is_active: bool = False,
    ) -> None:
        super().__init__(
            id=id,
            username=username,
            first_name=first_name,
            sur_name=sur_name,
            password=password,
            user_type=UserType.user,
            phone_number=phone_number,
            deleted_at=deleted_at,
        )
        self.is_active = is_active
