from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import (
    get_bedrock_client,
    get_s3_client,
    get_session,
    get_textract_client,
)
from ssmai_backend.models.user import User
from ssmai_backend.routers.users import fastapi_users
from ssmai_backend.schemas.products_schemas import (
    ExtractResultSchema,
    ProductInfoByAIResponse,
    ProductSchema,
    ProductsList,
    PublicProductSchema,
)
from ssmai_backend.schemas.root_schemas import FilterPage, Message
from ssmai_backend.services.products_service import (
    create_product_by_document_service,
    create_product_service,
    delete_product_by_id_service,
    generate_product_info_from_docs_pre_extracted_service,
    read_all_products_by_user_enterpryse_service,
    read_all_products_service,
    update_product_by_id_service,
    insert_products_with_csv_service
)

router = APIRouter(prefix="/products", tags=["products"])

T_Session = Annotated[AsyncSession, Depends(get_session)]

T_CurrentUser = Annotated[User, Depends(fastapi_users.current_user())]


@router.get("/all", response_model=ProductsList)
async def read_products(
    session: T_Session,
    filter: Annotated[FilterPage, Query()],
):
    return {"products": await read_all_products_service(session, filter)}


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    response_model=PublicProductSchema,
)
async def create_product(
    product: ProductSchema,
    session: T_Session,
    current_user: T_CurrentUser
):
    return await create_product_service(product, session, current_user)


@router.get("/all_by_user_enterpryse", response_model=ProductsList)
async def get_all_products_by_current_user(
    session: T_Session,
    filter: Annotated[FilterPage, Query()],
    current_user: T_CurrentUser
):
    return {"products": await read_all_products_by_user_enterpryse_service(
        session,
        filter,
        current_user
        )}


@router.delete(
    "/{product_id}", status_code=HTTPStatus.OK, response_model=Message
)
async def delete_product(
    session: T_Session,
    product_id: int,
    current_user: T_CurrentUser
):
    return {"message": await delete_product_by_id_service(
        product_id,
        session,
        current_user,)}


@router.put(
    "/{product_id}",
    status_code=HTTPStatus.CREATED,
    response_model=PublicProductSchema,
)
async def update_product_by_id(
    product: ProductSchema,
    product_id: int,
    session: T_Session,
    current_user: T_CurrentUser
):
    return await update_product_by_id_service(
        product_id,
        product,
        session,
        current_user
        )


@router.post('/extract_text_from_document/',
             status_code=HTTPStatus.CREATED,
             response_model=ExtractResultSchema)
async def extract_text_from_document(
    document: UploadFile,
    session: T_Session,
    s3_client=Depends(get_s3_client),
    textract_client=Depends(get_textract_client)
):
    return await create_product_by_document_service(
        document=document,
        session=session,
        s3_client=s3_client,
        textract_client=textract_client
    )


@router.post('/generate_product_by_ai_with_extract_id/{id_text_extract}',
             status_code=HTTPStatus.CREATED,
             response_model=ProductInfoByAIResponse)
async def generate_product_info_from_docs_pre_extracted(
    session: T_Session,
    id_text_extract: int,
    bedrock_client=Depends(get_bedrock_client),
):
    return await generate_product_info_from_docs_pre_extracted_service(
        session=session,
        bedrock_client=bedrock_client,
        id_text_extract=id_text_extract
    )


@router.post('/insert_batch', response_model=Message, status_code=HTTPStatus.CREATED)
async def insert_products_with_csv(
    session: T_Session,
    current_user: T_CurrentUser,
    csv_file: UploadFile = File(...)
):
    return await insert_products_with_csv_service(
        session, current_user, csv_file
    )
