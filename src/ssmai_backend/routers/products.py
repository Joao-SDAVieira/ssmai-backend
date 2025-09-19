from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import get_session
from ssmai_backend.models.user import User
from ssmai_backend.routers.users import fastapi_users
from ssmai_backend.schemas.products_schemas import (
    ProductSchema,
    ProductsList,
    PublicProductSchema,
)
from ssmai_backend.schemas.root_schemas import FilterPage, Message
from ssmai_backend.services.products_service import (
    create_product_service,
    delete_product_by_id_service,
    read_all_products_service,
    update_product_by_id_service,
)

router = APIRouter(prefix="/products", tags=["products"])

T_Session = Annotated[AsyncSession, Depends(get_session)]

T_CurrentUser = Annotated[User, Depends(fastapi_users.current_user())]


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    response_model=PublicProductSchema,
)
async def create_product(
    product: ProductSchema,
    session: T_Session,
    # current_user: T_CurrentUser
):
    # print(current_user.id)
    return await create_product_service(product, session)


@router.get("/", response_model=ProductsList)
async def read_products(
    session: T_Session, filter: Annotated[FilterPage, Query()]
):
    return {"products": await read_all_products_service(session, filter)}


@router.delete(
    "/{product_id}", status_code=HTTPStatus.OK, response_model=Message
)
async def delete_product(session: T_Session, product_id: int):
    return {"message": await delete_product_by_id_service(product_id, session)}


@router.put(
    "/{product_id}",
    status_code=HTTPStatus.CREATED,
    response_model=PublicProductSchema,
)
async def update_product_by_id(
    product: ProductSchema, product_id: int, session: T_Session
):
    return await update_product_by_id_service(product_id, product, session)
