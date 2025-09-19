from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from ssmai_backend.models.produto import table_registry


@table_registry.mapped
class User(SQLAlchemyBaseUserTable[int]):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    profile_image: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, onupdate=func.now(), server_default=func.now()
    )  # TODO: Análisar implementação de trigger para log
