from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()


@table_registry.mapped_as_dataclass
class Produto:
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    titulo: Mapped[str]
    preco_custo: Mapped[float]  # TODO: Adicionar custo na ia
    quantidade: Mapped[int]  # TODO: Adicionar na ia
    categoria: Mapped[str]  # TODO: possível enum, adicionar na ia
    status: Mapped[str]  # TODO: Arrumar isso para entrada e saida

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, onupdate=func.now(), server_default=func.now()
    )
