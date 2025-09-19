from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers

from ssmai_backend.models.user import User
from ssmai_backend.schemas.users_schemas import UserPublic
from ssmai_backend.security.user_settings import auth_backend
from ssmai_backend.services.user_service import (
    UserService,
    get_user_repository,
)

fastapi_users = FastAPIUsers[User, int](get_user_repository, [auth_backend])

router = APIRouter(prefix="/users", tags=["users"])
T_UserManager = Annotated[UserService, Depends(get_user_repository)]


@router.get("/{first_name}", response_model=list[UserPublic])
async def get_users_by_first_name(
    first_name: str, user_repository: T_UserManager
):
    return await user_repository.get_by_firts_name(first_name)
