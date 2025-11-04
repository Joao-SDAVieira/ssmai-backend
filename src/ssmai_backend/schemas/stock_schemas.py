from datetime import datetime

from pydantic import BaseModel

from ssmai_backend.enums.products_enums import MovementTypesEnum


class StockBase(BaseModel):
    id: int
    id_produtos: int
    quantidade_disponivel: int
    custo_medio: float
    created_at: datetime
    updated_at: datetime


class StockModel(StockBase):
   estoque_ideal: float


class MovimentBaseModel(BaseModel):
    quantidade: int


class ExitModel(MovimentBaseModel):
    ...


class EntryModel(MovimentBaseModel):
    preco_und: float


class MovimentModelResponse(MovimentBaseModel):
    id: int
    id_produtos: int
    preco_und: float
    tipo: MovementTypesEnum
    total: float
    date: datetime
    updated_at: datetime


class MovimentList(BaseModel):
    products: list[MovimentModelResponse]


class StockList(BaseModel):
    stocks: list[StockModel]
