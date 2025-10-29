from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import get_session
from ssmai_backend.models.user import User
from ssmai_backend.routers.users import fastapi_users
from ssmai_backend.schemas.root_schemas import FilterPage, Message
from ssmai_backend.schemas.stock_schemas import (
    EntryModel,
    ExitModel,
    MovimentList,
    MovimentModelResponse,
    StockList,
    StockModel,
)
from ssmai_backend.services.stock_service import (
    get_all_moviments_by_enterpryse_user_service,
    get_all_moviments_service,
    get_all_stock_by_user_enterpryse_service,
    get_all_stock_service,
    get_moviments_by_product_id_service,
    get_moviments_by_product_id_user_enterpryse_service,
    get_stock_by_product_id_service,
    register_entry_by_id_service,
    register_exit_by_id_service,
    insert_moviments_with_csv_service
)

router = APIRouter(prefix="/stock", tags=["stock"])

T_Session = Annotated[AsyncSession, Depends(get_session)]

T_CurrentUser = Annotated[User, Depends(fastapi_users.current_user())]


@router.get('/moviments/{product_id}',
            status_code=HTTPStatus.OK,
            response_model=MovimentList
            )
async def get_moviments_by_product_id(
    session: T_Session,
    product_id: int,
    filter: Annotated[FilterPage, Query()]
):
    return {"products": await get_moviments_by_product_id_service(
        product_id=product_id,
        session=session,
        filter=filter
    )}


@router.get(
    '/all',
    status_code=HTTPStatus.OK,
    response_model=StockList
    )
async def get_all_stock(
    session: T_Session,
    filter: Annotated[FilterPage, Query()]
):
    return {
        'stocks': await get_all_stock_service(
        session=session,
        filter=filter
    )
    }


@router.get(
    '/moviments/all',
    status_code=HTTPStatus.OK,
    response_model=MovimentList
    )
async def get_all_moviments(
    session: T_Session,
    filter: Annotated[FilterPage, Query()]
):
    return {"products": await get_all_moviments_service(
        session=session,
        filter=filter
    )
    }


@router.post('/entry/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=MovimentModelResponse)
async def register_entry_by_product_id(
    session: T_Session,
    product_id: int,
    entry: EntryModel,
    current_user: T_CurrentUser
):
    return await register_entry_by_id_service(
        product_id=product_id,
        session=session,
        moviment=entry,
        current_user=current_user
    )


@router.post('/exit/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=MovimentModelResponse)
async def register_exit_by_product_id(
    session: T_Session,
    product_id: int,
    exit: ExitModel,
    current_user: T_CurrentUser
):
    return await register_exit_by_id_service(
        product_id=product_id,
        session=session,
        moviment=exit,
        current_user=current_user
    )


@router.get('/moviments/user_enterpryse/{product_id}/',
            status_code=HTTPStatus.OK,
            response_model=MovimentList
            )
async def get_moviments_by_product_id_user_enterpryse(
    session: T_Session,
    product_id: int,
    filter: Annotated[FilterPage, Query()],
    current_user: T_CurrentUser,
):
    return {"products": await get_moviments_by_product_id_user_enterpryse_service(
        product_id=product_id,
        session=session,
        filter=filter,
        current_user=current_user,
    )}


@router.get(
    '/moviments/enterpryse_user/',
    status_code=HTTPStatus.OK,
    response_model=MovimentList
    )
async def get_all_moviments_by_enterpryse_user(
    session: T_Session,
    filter: Annotated[FilterPage, Query()],
    current_user: T_CurrentUser
):
    return {"products": await get_all_moviments_by_enterpryse_user_service(
        session=session,
        filter=filter,
        current_user=current_user
    )
    }


@router.get(
    '/{product_id}',
    status_code=HTTPStatus.OK,
    response_model=StockModel
    )
async def get_stock_by_product_id(
    product_id: int,
    session: T_Session,
    current_user: T_CurrentUser,
):
    return await get_stock_by_product_id_service(
        product_id=product_id,
        session=session,
        current_user=current_user
    )


@router.get(
    '/',
    status_code=HTTPStatus.OK,
    response_model=StockList
    )
async def get_all_stock_by_user_enterpryse(
    session: T_Session,
    filter: Annotated[FilterPage, Query()],
    current_user: T_CurrentUser
):
    return {
        'stocks': await get_all_stock_by_user_enterpryse_service(
        session=session,
        filter=filter,
        current_user=current_user,
    )
    }


@router.post('/moviments/insert_batch',
    response_model=Message,
    status_code=HTTPStatus.CREATED)
async def insert_moviments_with_csv(
    session: T_Session,
    current_user: T_CurrentUser,
    csv_file: UploadFile = File(...)
):
    return await insert_moviments_with_csv_service(
        session, current_user, csv_file
    )