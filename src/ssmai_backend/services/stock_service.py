from http import HTTPStatus

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, join, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.produto import (
    Empresa,
    Estoque,
    MovimentacoesEstoque,
    Produto,
)
from ssmai_backend.models.user import User
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.schemas.stock_schemas import (
    EntryModel,
    ExitModel,
    MovimentModelResponse,
)


async def get_stock_by_product_id(
    product_id: int,
    session: AsyncSession,
    current_user: User
):
    product = await session.scalar(select(Produto).where(Produto.id == product_id))

    if not product or (product.id_empresas != current_user.id_empresas):
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail="Product not found!"
        )
    stock_db = await session.scalar(
        select(Estoque).where(Estoque.id_produtos == product_id)
        )
    if not stock_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="Product or Stock not found!")
    return stock_db


# async def verify_if_products_exists(product_ids: list[int],
#                                     session: AsyncSession,
#                                     current_user: User):

#     qtd = session.scalar(select(func.count()).select_from(Produto).where(and_(Estoque.id_produtos == current_user.id_empresas, Produto.id)))


async def register_entry_by_id_service(
    product_id: int,
    session: AsyncSession,
    moviment: EntryModel | MovimentModelResponse,
    current_user: User,
    batch: bool = False
):
    await get_stock_by_product_id(product_id, session, current_user)
    if not batch:
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
    else:
        entry_db = MovimentacoesEstoque(
            id_produtos=product_id,
            tipo='Entrada',
            quantidade=moviment.quantidade,
            preco_und=moviment.preco_und,
            total=moviment.preco_und * moviment.quantidade
        )
        entry_db.updated_at = moviment.updated_at
        entry_db.date = moviment.date
        # entry_db.id = moviment.id
        session.add(entry_db)

    return entry_db


async def register_exit_by_id_service(
    product_id: int,
    session: AsyncSession,
    moviment: ExitModel | MovimentModelResponse,
    current_user: User,
    batch: bool = False
):
    stock_db = await get_stock_by_product_id(product_id, session, current_user)
    if not batch:
        if stock_db.quantidade_disponivel < moviment.quantidade:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                                detail='Quantity unavailable')
        exit_db = MovimentacoesEstoque(
            id_produtos=product_id,
            tipo='Saida',
            quantidade=moviment.quantidade,
            preco_und=stock_db.custo_medio,
            total=stock_db.custo_medio * moviment.quantidade
        )
        session.add(exit_db)
        await session.commit()
        await session.refresh(exit_db)
    else:
        exit_db = MovimentacoesEstoque(
            id_produtos=product_id,
            tipo='Saida',
            quantidade=moviment.quantidade,
            preco_und=stock_db.custo_medio,
            total=stock_db.custo_medio * moviment.quantidade
        )
        exit_db.updated_at = moviment.updated_at
        exit_db.date = moviment.date
        # exit_db.id = moviment.id
        session.add(exit_db)

    return exit_db


async def get_moviments_by_product_id_service(
    product_id: int,
    session: AsyncSession,
    filter: FilterPage,
):
    return await session.scalars(
        select(MovimentacoesEstoque).where(
            MovimentacoesEstoque.id_produtos == product_id
            ).offset(filter.offset).limit(filter.limit)
    )


async def get_moviments_by_product_id_user_enterpryse_service(
    product_id: int,
    session: AsyncSession,
    filter: FilterPage,
    current_user: User
):
    statement = (
        select(MovimentacoesEstoque)
        .select_from(
            join(MovimentacoesEstoque, Produto, MovimentacoesEstoque.id_produtos == Produto.id)
            .join(Empresa, Produto.id_empresas == Empresa.id)
        )
        .where(
            and_(Empresa.id == current_user.id_empresas,
                 MovimentacoesEstoque.id_produtos == product_id)
            )
        .limit(filter.limit).offset(filter.offset)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def get_all_moviments_service(
    session: AsyncSession,
    filter: FilterPage,
):
    return await session.scalars(
        select(MovimentacoesEstoque).offset(filter.offset).limit(filter.limit)
    )


async def get_all_moviments_by_enterpryse_user_service(
    session: AsyncSession,
    filter: FilterPage,
    current_user: User
):
    statement = (
        select(MovimentacoesEstoque)
        .select_from(
            join(MovimentacoesEstoque, Produto, MovimentacoesEstoque.id_produtos == Produto.id)
            .join(Empresa, Produto.id_empresas == Empresa.id)
        )
        .where(Empresa.id == current_user.id_empresas)
        .limit(filter.limit).offset(filter.offset)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def get_stock_by_product_id_service(
    product_id: int,
    session: AsyncSession,
    current_user: User
):
    return await get_stock_by_product_id(
        product_id,
        session,
        current_user,
        )


async def get_all_stock_service(
    session: AsyncSession,
    filter: FilterPage,
):
    return await session.scalars(
        select(Estoque).offset(filter.offset).limit(filter.limit)
    )


async def get_all_stock_by_user_enterpryse_service(
    session: AsyncSession,
    filter: FilterPage,
    current_user: User
):
    statement = (
        select(Estoque)
        .select_from(
            join(Estoque, Produto, Estoque.id_produtos == Produto.id)
            .join(Empresa, Produto.id_empresas == Empresa.id)
        )
        .where(Empresa.id == current_user.id_empresas)
        .limit(filter.limit).offset(filter.offset)
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def insert_moviments_with_csv_service(
    session: AsyncSession,
    current_user: User,
    csv_file: UploadFile
):
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Unexpected format"
        )
    contents = await csv_file.read()
    try:
        df_moviments = pd.read_csv(pd.io.common.BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Unable to read CSV"
        )
    required_columns = {"id", "id_produtos", "tipo", "quantidade", "preco_und", "total", "date", "updated_at"}
    if not required_columns.issubset(df_moviments.columns):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"CSV deve conter as colunas: {', '.join(required_columns)}"
        )
    try:
        for _, row in df_moviments.iterrows():
            tipo = row["tipo"]
            product_id = row["id_produtos"]
            if tipo in ("Entrada", "entrada"):
                moviment = MovimentModelResponse(
                    id=row["id"],
                    id_produtos=row['id_produtos'],
                    tipo='Entrada',
                    quantidade=row["quantidade"],
                    preco_und=row["preco_und"],
                    total=row['total'],
                    date=row['date'],
                    updated_at=row['updated_at']
                )
                await register_entry_by_id_service(product_id, session, moviment, current_user, batch=True)
            elif tipo in ("Saida", 'saida'):
                moviment = MovimentModelResponse(
                    id=row["id"],
                    id_produtos=row['id_produtos'],
                    tipo='Saida',
                    quantidade=row["quantidade"],
                    preco_und=row["preco_und"],
                    total=row['total'],
                    date=row['date'],
                    updated_at=row['updated_at']
                )
                await register_exit_by_id_service(product_id, session, moviment, current_user, batch=True)
            else:
                print(row["id"], row['id_produtos'])
                raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='Saida, Entrada ou Outro')
        await session.commit()
        print('alow')
    except Exception as e:
        await session.rollback()
        print(type(e))
        print(e)
        print('aloo')
        raise HTTPException(status_code=500, detail='Fail')

    return {'message': 'success'}
