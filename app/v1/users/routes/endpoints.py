from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.deps.providers import get_uow
from app.v1.users.deps.providers import get_jwt_service, get_password_hasher
from src.users.ports.security.jwt import JwtPort
from src.users.ports.security.password_hasher import PasswordHasherPort
from src.users.application.use_cases.login import login_use_case
from src.users.domain.entities.base_user import BaseUser
from src.base.ports.unit_of_work import AsyncUnitOfWork
from src.base.exceptions import NotFoundException
from app.v1.users.deps.get_current_user import get_current_user
import app.v1.users.schemas.v1_responses as rsm

router = APIRouter(prefix="", tags=["users"])


@router.get("/auth/current_user", response_model=rsm.V1BaseUserResponse)
async def current_user(
    user: BaseUser = Depends(get_current_user),
):
    return user


@router.post("/auth/login", response_model=rsm.V1LoginResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    uow: AsyncUnitOfWork = Depends(get_uow),
    jwt_service: JwtPort = Depends(get_jwt_service),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
):
    async with uow:
        token = await login_use_case(
            username=form.username,
            password=form.password,
            uow=uow,
            jwt_service=jwt_service,
            password_hasher=password_hasher,
        )

        return rsm.V1LoginResponse(access_token=token)


@router.get("/admins/{admin_id}", response_model=rsm.V1BaseUserResponse)
async def get_admin(
    admin_id: int,
    uow: AsyncUnitOfWork = Depends(get_uow),
):
    """Get admin by ID. Caching is handled by the repository."""
    from src.users.domain.entities.admin import Admin

    async with uow:
        admin = await uow.admin_repo.get_by_id(id=admin_id)
        if admin is None:
            raise NotFoundException(
                detail=f"Admin with id {admin_id} not found", entity=Admin
            )
        return admin
