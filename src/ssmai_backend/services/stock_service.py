from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ssmai_backend.schemas.stock_schemas import EntryModel, ExitModel, StockModel
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.models.produto import Estoque, MovimentacoesEstoque


async def get_stock_by_product_id(
    product_id: int,
    session: AsyncSession,
):
    stock_db = await session.scalar(
        select(Estoque).where(Estoque.id_produtos == product_id)
        )
    if not stock_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="Product or Stock not found!")
    return stock_db


async def register_entry_by_id_service(
    product_id: int,
    session: AsyncSession,
    moviment: EntryModel,
):
    await get_stock_by_product_id(product_id, session)

    entry_db = MovimentacoesEstoque(
        id_produtos=product_id,
        tipo='Entrada',
        quantidade=moviment.quantidade,
        preco_und=moviment.preco_und,
        total=moviment.preco_und * moviment.quantidade
    )
    session.add(entry_db)
    await session.commit()
    await session.refresh(entry_db)
    return entry_db


async def register_exit_by_id_service(
    product_id: int,
    session: AsyncSession,
    moviment: ExitModel,
):
    stock_db = await get_stock_by_product_id(product_id, session)
    if stock_db.quantidade_disponivel < moviment.quantidade:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail='Quantity unavailable')
    entry_db = MovimentacoesEstoque(
        id_produtos=product_id,
        tipo='Saida',
        quantidade=moviment.quantidade,
        preco_und=stock_db.custo_medio,
        total=stock_db.custo_medio * moviment.quantidade
    )
    session.add(entry_db)
    await session.commit()
    await session.refresh(entry_db)
    return entry_db


async def get_moviments_by_product_id_service(
    product_id: int,
    session:AsyncSession,
    filter: FilterPage,
):
    return await session.scalars(
        select(MovimentacoesEstoque).where(
            MovimentacoesEstoque.id_produtos == product_id
            ).offset(filter.offset).limit(filter.limit)
    )


async def get_all_moviments_service(
    session:AsyncSession,
    filter: FilterPage,
):
    return await session.scalars(
        select(MovimentacoesEstoque).offset(filter.offset).limit(filter.limit)
    )


async def get_stock_by_product_id_service(
    product_id: int,
    session:AsyncSession,
):
    return await get_stock_by_product_id(
        product_id,
        session,
        )


async def get_all_stock_service(
    session:AsyncSession,
    filter: FilterPage,
):
    return await session.scalars(
        select(Estoque).offset(filter.offset).limit(filter.limit)
    )