from contextlib import contextmanager
from datetime import datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from ssmai_backend.app import app
from ssmai_backend.database import get_session
from ssmai_backend.models.produto import Produto, table_registry


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def engine():
    with PostgresContainer("postgres:17", driver="psycopg") as postgres:
        yield create_async_engine(postgres.get_connection_url())


@pytest_asyncio.fixture
async def session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@contextmanager
def _mock_db_time(*, model, time=datetime(2025, 9, 7)):
    def fake_time_hook(mapper, connection, target: Produto):
        if hasattr(target, "created_at") and hasattr(target, "updated_at"):
            target.created_at = time
            target.updated_at = time

    event.listen(model, "before_insert", fake_time_hook)

    yield time

    event.remove(model, "before_insert", fake_time_hook)


@pytest.fixture
def mock_db_time():
    return _mock_db_time


@pytest_asyncio.fixture
async def product(session: AsyncSession):
    product = Produto(
        titulo="Mesa",
        preco=85.5,
        quantidade=1,
        categoria="Móvel",
        status="A venda",
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    return product
