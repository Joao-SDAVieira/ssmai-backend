from http import HTTPStatus

from fastapi import APIRouter, Depends, Query
from typing import Annotated
from ssmai_backend.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.schemas.stock_schemas import MovimentModel, MovimentModelResponse, MovimentList
from ssmai_backend.services.stock_service import (register_moviment_by_id_service,
                                                  get_moviments_by_product_id_service,
                                                  get_all_moviments_service)


router = APIRouter(prefix="/stock", tags=["stock"])

T_Session = Annotated[AsyncSession, Depends(get_session)]


#TODO: fazer validações de usuário ou empresa. Validar com triggers
@router.post('/entry/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=MovimentModelResponse)
async def register_entry_by_product_id(
    session: T_Session,
    product_id: int,
    entry: MovimentModel
):
    return await register_moviment_by_id_service(
        product_id=product_id,
        session=session,
        moviment=entry,
        type = "entrada",
    )


@router.post('/exit/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=MovimentModelResponse)
async def register_exit_by_product_id(
    session: T_Session,
    product_id: int,
    exit: MovimentModel
):
    return await register_moviment_by_id_service(
        product_id=product_id,
        session=session,
        moviment=exit,
        type = "saida",
    )


#TODO: implementar filtro por empresa
@router.get('{product_id}',
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
    '',
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
