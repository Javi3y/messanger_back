from src.base.exceptions import UnauthorizedException
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.users.ports.security.jwt import JwtPort
from src.users.ports.security.password_hasher import PasswordHasherPort


async def authenticate_user(
    *,
    username: str,
    password: str,
    uow: AsyncUnitOfWork,
    jwt_service: JwtPort,
    password_hasher: PasswordHasherPort,
) -> str:
    user = await uow.base_user_repo.get_by_username(username=username)
    if not user or not password_hasher.verify(password, user.password):
        raise UnauthorizedException("Invalid username or password")

    return jwt_service.create_access_token(subject=user.username)
