from datetime import datetime
from pydantic import BaseModel
from ssmai_backend.schemas.stock_schemas import StockModel


class AnalysisSchema(BaseModel):
    diary_average: float
    demanda_leadtime: float
    safety_stock: float
    estoque_ideal: float
    pedir: float

class HistoricoItem(BaseModel):
    data: datetime
    estoque: float

class PrevisaoItem(BaseModel):
    data: datetime
    saida_prevista: int

class PrevisoesResponse(BaseModel):
    historico: list[HistoricoItem]
    previsoes: list[PrevisaoItem]

class IndicatorSchema(BaseModel):
    difference_percent: float
    difference_quantity: int
    bigger_than_expected: bool
    cash_loss: float

class IdealStockSchema(BaseModel):
    indicators: IndicatorSchema
    stock: StockModel