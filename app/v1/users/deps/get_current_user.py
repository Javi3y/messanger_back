from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.container import ApplicationContainer
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.users.ports.security.jwt import JwtPort
from src.users.domain.entities.base_user import BaseUser
from src.users.application.services.auth_user import get_current_user_from_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/auth/login")


@inject
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    uow: AsyncUnitOfWork = Depends(Provide[ApplicationContainer.unit_of_work]),
    jwt_service: JwtPort = Depends(Provide[ApplicationContainer.jwt_service]),
) -> BaseUser:
    return await get_current_user_from_token(
        token=token, uow=uow, jwt_service=jwt_service
    )
