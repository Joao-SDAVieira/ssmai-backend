from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.produto import Produto
from ssmai_backend.schemas.products_schemas import ProductSchema
from ssmai_backend.schemas.root_schemas import FilterPage


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
