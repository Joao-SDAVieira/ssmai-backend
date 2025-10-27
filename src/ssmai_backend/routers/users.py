from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi_users import FastAPIUsers

from ssmai_backend.models.user import User
from ssmai_backend.schemas.users_schemas import UserPublic
from ssmai_backend.security.user_settings import auth_backend
from ssmai_backend.services.user_service import (
    UserService,
    get_user_repository,
)

fastapi_users = FastAPIUsers[User, int](get_user_repository, [auth_backend])
current_superuser = fastapi_users.current_user(superuser=True)

router = APIRouter(prefix="/users", tags=["users"])
T_UserManager = Annotated[UserService, Depends(get_user_repository)]


async def inject_creator(
    request: Request,
    creator: User = Depends(current_superuser),
):
    request.state.creator = creator


@router.get("/", response_model=list[UserPublic])
async def get_all_users(
    user_repository: T_UserManager
):
    return await user_repository.get_all()
