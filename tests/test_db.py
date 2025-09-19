from dataclasses import asdict

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.produto import Produto


@pytest.mark.asyncio
async def test_create_produto(session: AsyncSession, mock_db_time):
    with mock_db_time(model=Produto) as time:
        new_produto = Produto(
            titulo="Mesa",
            preco=85.5,
            quantidade=1,
            categoria="Móvel",
            status="A venda",
        )
        session.add(new_produto)
        await session.commit()

        produto = await session.scalar(
            select(Produto).where(Produto.titulo == "Mesa")
        )

    assert asdict(produto) == {
        "id": 1,
        "titulo": "Mesa",
        "preco": 85.5,
        "quantidade": 1,
        "categoria": "Móvel",
        "status": "A venda",
        "created_at": time,
        "updated_at": time,
    }
