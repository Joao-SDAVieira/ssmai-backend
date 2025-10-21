from http import HTTPStatus

from fastapi import APIRouter, Depends, Query
from typing import Annotated
from ssmai_backend.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.schemas.stock_schemas import MovimentModelResponse, MovimentList, EntryModel, ExitModel, StockModel, StockList
from ssmai_backend.services.stock_service import (register_entry_by_id_service,
                                                  register_exit_by_id_service,
                                                  get_moviments_by_product_id_service,
                                                  get_all_moviments_service,
                                                  get_stock_by_product_id_service,
                                                  get_all_stock_service)


router = APIRouter(prefix="/stock", tags=["stock"])

T_Session = Annotated[AsyncSession, Depends(get_session)]


#TODO: fazer validações de usuário ou empresa. Validar com triggers
@router.post('/entry/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=MovimentModelResponse)
async def register_entry_by_product_id(
    session: T_Session,
    product_id: int,
    entry: EntryModel
):
    return await register_entry_by_id_service(
        product_id=product_id,
        session=session,
        moviment=entry,
    )


@router.post('/exit/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=MovimentModelResponse)
async def register_exit_by_product_id(
    session: T_Session,
    product_id: int,
    exit: ExitModel
):
    return await register_exit_by_id_service(
        product_id=product_id,
        session=session,
        moviment=exit,
    )


#TODO: implementar filtro por empresa
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
    ) }


#TODO: implementar filtro por empresa para n trazer tudo
@router.get(
    '/moviments/',
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


@router.get(
    '/{product_id}/',
    status_code=HTTPStatus.OK,
    response_model=StockModel
    )
async def get_stock_by_product_id(
    product_id: int,
    session: T_Session,
):
    return await get_stock_by_product_id_service(
        product_id=product_id,
        session=session,
        filter=filter
    )


@router.get(
    '/',
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
