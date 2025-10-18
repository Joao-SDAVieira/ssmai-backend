from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from ssmai_backend.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ssmai_backend.models.produto import Estoque, MovimentacoesEstoque
from ssmai_backend.schemas.root_schemas import Message
from ssmai_backend.schemas.stock_schemas import EntryModel, EntryModelResponse



router = APIRouter(prefix="/stock", tags=["stock"])

T_Session = Annotated[AsyncSession, Depends(get_session)]


def register_entry_or_exit():
    ...


#TODO: fazer validações de usuário ou empresa
@router.post('/{product_id}',
             status_code=HTTPStatus.CREATED,
             response_model=EntryModelResponse)
async def register_entry_by_product_id(
    session: T_Session,
    product_id: int,
    entry: EntryModel
):
    stock_db = await session.scalar(
        select(Estoque).where(Estoque.id_produtos == product_id)
        )
    if not stock_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="Product or Stock not found!")
    
    entry_db = MovimentacoesEstoque(
        id_produtos=product_id,
        tipo="Entrada",
        quantidade=entry.quantidade,
        preco_und=entry.preco_und,
        total=entry.preco_und * entry.quantidade
    )
    session.add(entry_db)
    await session.commit()
    await session.refresh(entry_db)

    return entry_db


