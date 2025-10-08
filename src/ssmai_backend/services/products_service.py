from http import HTTPStatus
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.document import Document
from ssmai_backend.models.produto import Produto
from ssmai_backend.schemas.products_schemas import ProductSchema
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.settings import Settings


async def create_product_service(
    product: ProductSchema, session: AsyncSession
):
    db_product = await session.scalar(
        select(Produto).where(Produto.titulo == product.titulo)
    )

    if db_product:  # TODO: alterar para o mesmo user
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Product already exists!"
        )

    db_product = Produto(
        titulo=product.titulo,
        preco=product.preco,
        quantidade=product.quantidade,
        categoria=product.categoria,
        status=product.status,
    )

    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


async def read_all_products_service(session: AsyncSession, filter: FilterPage):
    return await session.scalars(
        select(Produto).offset(filter.offset).limit(filter.limit)
    )


# TODO: para endpoints de alteração, verificar se
#  o produto é do usuário que criou (perm)


async def delete_product_by_id_service(id: int, session: AsyncSession):
    product_db = await find_by_product_by_id(id, session)

    # TODO: se usuário é dono do produto
    await session.delete(product_db)
    await session.commit()
    return "Product deleted!"


async def update_product_by_id_service(
    id: int, product: ProductSchema, session: AsyncSession
):
    product_db: Produto = await find_by_product_by_id(id, session)
    product_with_same_titulo = await session.scalar(
        select(Produto).where(Produto.titulo == product.titulo)
    )
    if (
        product_with_same_titulo
        and product_with_same_titulo.id != product_db.id
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Product already exists!"
        )

    product_db.titulo = product.titulo
    product_db.categoria = product.categoria
    product_db.preco = product.preco
    product_db.quantidade = product.quantidade
    product_db.status = product.status
    await session.commit()
    await session.refresh(product_db)
    return product_db


async def find_by_product_by_id(id: int, session: AsyncSession):
    product_db = await session.scalar(select(Produto).where(Produto.id == id))
    if not product_db:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Product with id {id} not found!",
        )
    return product_db


async def create_product_by_document_service(
    document: UploadFile,
    session: AsyncSession,
    s3_client,
    textract_client
):
    SETTINGS = Settings()
    IMAGE_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
    ext = document.filename.split('.')[-1]

    EMPRESA_DEFAULT_ID = 1  # TODO: Ajustar

    filename_with_ext = (
        f'uploads/{EMPRESA_DEFAULT_ID}/documents_to_extract/{uuid4()}.{ext}'
    )

    if document.content_type in IMAGE_MIME_TYPES:
        await s3_client.upload_fileobj(
            document.file,
            SETTINGS.S3_BUCKET,
            filename_with_ext,
            ExtraArgs={'ContentType': 'image/jpeg'},
        )

    document_db = Document(extracted=False,
             document_path=f'https://{SETTINGS.S3_BUCKET}.s3.{SETTINGS.REGION}.amazonaws.com/{filename_with_ext}')
    session.add(document_db)
    await session.commit()

    response = await textract_client.detect_document_text(
        Document={
            "S3Object": {
                "Bucket": SETTINGS.S3_BUCKET,
                "Name": filename_with_ext
            }
        }
    )
    text_clean = "\n".join(
        block["Text"]
        for block in response["Blocks"] if block["BlockType"] in ("LINE", "WORD")
    )
    document_db.extract_result = text_clean
    document_db.extracted = True
    await session.commit()
    await session.refresh(document_db)

    return document_db
