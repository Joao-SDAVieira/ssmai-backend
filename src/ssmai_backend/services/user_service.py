from fastapi import Depends
from fastapi_users import (
    BaseUserManager,
    IntegerIDMixin,
    InvalidPasswordException,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select

from ssmai_backend.models.user import User
from ssmai_backend.schemas.users_schemas import BaseUserSchema, UserSchema
from ssmai_backend.security.user_settings import get_user_db

SECRET_KEY = "SECRET"


class UserService(IntegerIDMixin, BaseUserManager[User, int]):
    verification_token_secret = SECRET_KEY
    reset_password_token_secret = SECRET_KEY

    @classmethod
    async def validate_password(
        self,
        password: str,
        user: User,
    ) -> None:
        MIN_LENGTH_PASSWORD = 8
        if len(password) < MIN_LENGTH_PASSWORD:
            raise InvalidPasswordException(
                reason="Password should be at least 8 characters"
            )
        if user.email in password:
            raise InvalidPasswordException(
                reason="Password should not contain e-mail"
            )

    async def create(
        self,
        user_create: BaseUserSchema | UserSchema,
        safe=False,
        request=None,
    ):
        creator = None
        if request and hasattr(request, "state"):
            creator = getattr(request.state, "creator", None)

        if creator and creator.is_superuser:
            user_create = UserSchema(
                **user_create.model_dump(), id_empresas=creator.id_empresas
            )
        return await super().create(user_create, safe, request)

    async def get_all(self):
        user_db: SQLAlchemyUserDatabase = self.user_db
        users = await user_db.session.scalars(
            select(user_db.user_table)
        )
        return users


async def get_user_repository(user_db=Depends(get_user_db)):
    yield UserService(user_db)
