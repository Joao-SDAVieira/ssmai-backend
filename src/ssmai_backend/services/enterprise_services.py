import random
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users.exceptions import UserAlreadyExists

from ssmai_backend.models.produto import Empresa
from ssmai_backend.models.user import User
from ssmai_backend.schemas.enterpryse_schemas import (
    EnterpryseResponseModel,
    EnterpryseSchema,
)
from ssmai_backend.schemas.users_schemas import UserAdminSchema, UserSchema
from ssmai_backend.services.user_service import UserService


async def get_enterpryse_by_user(user: User, session: AsyncSession):
    enterpryse = await session.scalar(select(Empresa).where(Empresa.id == User.id))
    if not enterpryse:
        raise HTTPException(HTTPStatus.BAD_REQUEST,
                            status_code="Enterpryse not found to this user")
    return enterpryse


async def create_enterpryse_service(
    session: AsyncSession,
    enterpryse: EnterpryseSchema,
    user_repository: UserService
):
    enterpryse_exists = await session.scalar(
        select(Empresa).where(Empresa.nome == enterpryse.nome)
        )
    if enterpryse_exists:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Enterpryse already exists!"
        )
    enterpryse_dict = enterpryse.model_dump()
    enterpryse_dict.pop('email')
    enterpryse_db = Empresa(**enterpryse_dict)

    session.add(enterpryse_db)
    await session.commit()
    await session.refresh(enterpryse_db)

    password_default = random.randint(1000, 9999)
    user_admin_default = UserSchema(
        id_empresas=enterpryse_db.id,
        username=f'{enterpryse.nome.capitalize()}Admin',
        name=f'{enterpryse.nome.capitalize()}Admin',
        last_name='',
        description='User created at enterprise creation',
        email=enterpryse.email,
        profile_image='',
        password=f'{enterpryse.nome.capitalize()}@{password_default}',
        is_superuser=True
        )
    try:
        user_db = await user_repository.create(user_create=user_admin_default)
    except UserAlreadyExists:
        raise HTTPException(status_code=HTTPStatus.CONFLICT,
                            detail='Enterpryse already exists!')

    session.add(user_db)
    await session.commit()
    await session.refresh(user_db)
    user_admin_default = UserAdminSchema(**user_admin_default.model_dump(), clean_password=f'{enterpryse.nome.capitalize()}@{password_default}')
    user_admin_default.id = user_db.id
    enterpryse = EnterpryseResponseModel(nome=enterpryse_db.nome,
                                         ramo=enterpryse_db.ramo,
                                         id=enterpryse_db.id,
                                         created_at=enterpryse_db.created_at,
                                         updated_at=enterpryse_db.updated_at,
                                         user_admin=user_admin_default,
                                         email=user_db.email
                                         )

    return enterpryse


async def get_enterpryse_by_id_service(
    session: AsyncSession,
    enterpryse_id: int
):
    enterpryse_db = await session.scalar(
        select(Empresa).where(Empresa.id == enterpryse_id)
        )

    return enterpryse_db


async def get_all_enterpryse_service(
    session: AsyncSession,
):
    enterpryses = await session.scalars(select(Empresa))

    return enterpryses


async def delete_enterpryse_by_id_service(
    session: AsyncSession,
    enterpryse_id: int
):
    enterpryse_db = await session.scalar(
        select(Empresa).where(Empresa.id == enterpryse_id)
        )
    if not enterpryse_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Enterpryse is not found!"
        )
    await session.delete(enterpryse_db)
    await session.commit()
    return {'message': 'Deleted!'}
