from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.users.ports.security.jwt import JwtPort
from src.users.ports.security.password_hasher import PasswordHasherPort
from src.users.application.services.auth_service import authenticate_user


async def login_use_case(
    *,
    username: str,
    password: str,
    uow: AsyncUnitOfWork,
    jwt_service: JwtPort,
    password_hasher: PasswordHasherPort,
) -> str:
    return await authenticate_user(
        username=username,
        password=password,
        uow=uow,
        jwt_service=jwt_service,
        password_hasher=password_hasher,
    )
