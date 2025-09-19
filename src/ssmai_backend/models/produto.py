from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()


@table_registry.mapped_as_dataclass
class Produto:
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    titulo: Mapped[str]
    # TODO: Criar regra para mesmo usuário não ter produtos com o mesmo titulo
    preco: Mapped[float]
    quantidade: Mapped[int]
    categoria: Mapped[str]  # TODO: possível enum
    status: Mapped[str]  # TODO: Enum

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, onupdate=func.now(), server_default=func.now()
    )  # TODO: Análisar implementação de trigger para log
