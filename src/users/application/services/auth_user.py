from datetime import datetime, timezone

from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.base.exceptions import NotFoundException, UnauthorizedException
from src.users.ports.security.jwt import JwtPort
from src.users.domain.entities.base_user import BaseUser


async def get_current_user_from_token(
    *,
    token: str,
    uow: AsyncUnitOfWork,
    jwt_service: JwtPort,
) -> BaseUser:
    payload = jwt_service.decode(token)

    username = payload.get("sub")
    exp = payload.get("exp")

    if not username or not exp:
        raise UnauthorizedException("Invalid token")

    if datetime.now(timezone.utc).timestamp() > float(exp):
        raise UnauthorizedException("Token expired")

    async with uow:
        user = await uow.base_user_repo.get_by_username(username=username)
        if not user:
            raise NotFoundException(BaseUser)
        return user
