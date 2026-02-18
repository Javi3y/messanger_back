from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.container import ApplicationContainer
from src.users.ports.security.jwt import JwtPort
from src.users.ports.security.password_hasher import PasswordHasherPort


@inject
def get_jwt_service(
    jwt_service: JwtPort = Depends(Provide[ApplicationContainer.jwt_service]),
) -> JwtPort:
    return jwt_service


@inject
def get_password_hasher(
    password_hasher: PasswordHasherPort = Depends(
        Provide[ApplicationContainer.password_hasher]
    ),
) -> PasswordHasherPort:
    return password_hasher
