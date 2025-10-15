from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from ssmai_backend.models.produto import table_registry


@table_registry.mapped
class Document:
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    extracted: Mapped[bool]
    document_path: Mapped[str]
    extract_result: Mapped[str] = mapped_column(default=None, nullable=True)
    ai_result: Mapped[str] = mapped_column(default=None, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
