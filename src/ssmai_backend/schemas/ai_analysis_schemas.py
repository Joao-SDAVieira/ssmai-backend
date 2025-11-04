from datetime import datetime
from pydantic import BaseModel


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
    estoque_previsto: int

class PrevisoesResponse(BaseModel):
    historico: list[HistoricoItem]
    previsoes: list[PrevisaoItem]