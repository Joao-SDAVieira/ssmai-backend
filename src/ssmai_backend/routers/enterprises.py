from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import get_session
from ssmai_backend.schemas.enterpryse_schemas import (
    EnterpryseResponseModel,
    EnterpryseSchema,
    EnterpryseGet
)
from ssmai_backend.schemas.root_schemas import Message
from ssmai_backend.services.enterprise_services import (
    create_enterpryse_service,
    delete_enterpryse_by_id_service,
    get_all_enterpryse_service,
    get_enterpryse_by_id_service,
)
from ssmai_backend.services.user_service import (
    UserService,
    get_user_repository,
)

router = APIRouter(prefix="/enterpryse", tags=["enterpryses"])

T_Session = Annotated[AsyncSession, Depends(get_session)]
T_UserManager = Annotated[UserService, Depends(get_user_repository)]


@router.post('/',
             status_code=HTTPStatus.CREATED,
             response_model=EnterpryseResponseModel)
async def create_enterpryse(
    session: T_Session,
    enterpryse: EnterpryseSchema,
    user_repository: T_UserManager
):
    return await create_enterpryse_service(
        session=session,
        enterpryse=enterpryse,
        user_repository=user_repository
    )


@router.get('/{enterpryse_id}',
             status_code=HTTPStatus.CREATED,
             response_model=EnterpryseGet)
async def get_enterpryse_by_id(
    session: T_Session,
    enterpryse_id: int
):
    return await get_enterpryse_by_id_service(
        session=session,
        enterpryse_id=enterpryse_id
    )


@router.get('/',
             status_code=HTTPStatus.CREATED,
             response_model=list[EnterpryseGet])
async def get_all_enterpryse(
    session: T_Session,
):
    return await get_all_enterpryse_service(
        session=session,
    )


@router.delete('/{enterpryse_id}',
             status_code=HTTPStatus.CREATED,
             response_model=Message,)
async def delete_enterpryse_by_id(
    session: T_Session,
    enterpryse_id: int,
):
    return await delete_enterpryse_by_id_service(
        session=session,
        enterpryse_id=enterpryse_id,
    )
