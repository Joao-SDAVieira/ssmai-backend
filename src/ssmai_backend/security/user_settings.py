from fastapi import Depends
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import get_session
from ssmai_backend.models.user import User

SECRET_KEY = "SECRET"

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy():
    return JWTStrategy(
        secret=SECRET_KEY, lifetime_seconds=3600, algorithm="HS256"
    )


async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)


auth_backend = AuthenticationBackend(
    name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy
)
