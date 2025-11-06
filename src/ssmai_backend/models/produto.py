from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, registry

from ssmai_backend.enums.products_enums import MovementTypesEnum

table_registry = registry()


@table_registry.mapped_as_dataclass
class Produto:
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    id_empresas: Mapped[int] = mapped_column(
        ForeignKey('empresas.id', ondelete='CASCADE', name="fk_produtos_empresas"),
        nullable=False
    )
    nome: Mapped[str]
    categoria: Mapped[str]
    image: Mapped[str] = mapped_column(nullable=True, default=None, init=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, onupdate=func.now(), server_default=func.now()
    )


@table_registry.mapped_as_dataclass
class Estoque:
    __tablename__ = "estoque"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    id_produtos: Mapped[int] = mapped_column(
        ForeignKey('produtos.id', ondelete='CASCADE'), nullable=False
    )
    quantidade_disponivel: Mapped[int]
    custo_medio: Mapped[float] = mapped_column(nullable=False)
    estoque_ideal: Mapped[float] = mapped_column(nullable=True, init=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(),
        init=False, server_default=func.now()
    )


@table_registry.mapped_as_dataclass
class MovimentacoesEstoque:
    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    id_produtos: Mapped[int] = mapped_column(
        ForeignKey('produtos.id', ondelete='CASCADE'), nullable=False
    )
    tipo: Mapped[MovementTypesEnum] = mapped_column(nullable=False)
    quantidade: Mapped[int] = mapped_column(nullable=False)
    preco_und: Mapped[float] = mapped_column(nullable=False)
    total: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(),
        init=False, server_default=func.now()
    )


@table_registry.mapped_as_dataclass
class Empresa:
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    nome: Mapped[str] = mapped_column(nullable=True, unique=True)
    ramo: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(),
        init=False, server_default=func.now()
    )


@table_registry.mapped_as_dataclass
class Previsoes:
    __tablename__ = "previsoes"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    id_produtos: Mapped[int] = mapped_column(
        ForeignKey('produtos.id', ondelete='CASCADE'), nullable=False
    )
    data: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    saida_prevista: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(),
        init=False, server_default=func.now()
    )
