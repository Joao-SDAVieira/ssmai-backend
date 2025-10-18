from datetime import datetime
from pydantic import BaseModel
from ssmai_backend.enums.products_enums import MovementTypesEnum

class StockModel(BaseModel):
    id: int
    id_produtos: int
    quantidade_disponivel: int
    custo_medio: float
    created_at: datetime
    updated_at: datetime


class EntryModel(BaseModel):
    quantidade: int
    preco_und: float


class EntryModelResponse(EntryModel):
    id: int
    id_produtos: int
    tipo: MovementTypesEnum
    total: float
    date: datetime
    updated_at: datetime
