from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ssmai_backend.schemas.stock_schemas import MovimentModel
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.models.produto import Estoque, MovimentacoesEstoque

async def register_moviment_by_id_service(
    product_id: int,
    session: AsyncSession,
    moviment: MovimentModel,
    type: str,
):
    stock_db = await session.scalar(
        select(Estoque).where(Estoque.id_produtos == product_id)
        )
    if not stock_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="Product or Stock not found!")
    
    entry_db = MovimentacoesEstoque(
        id_produtos=product_id,
        tipo=type,
        quantidade=moviment.quantidade,
        preco_und=moviment.preco_und,
        total=moviment.preco_und * moviment.quantidade
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