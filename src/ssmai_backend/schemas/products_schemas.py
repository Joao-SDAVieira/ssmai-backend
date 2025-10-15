from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ProductSchema(BaseModel):
    titulo: str
    preco: float # TODO: adicionar
    quantidade: int
    categoria: str
    status: str  # TODO: Retirar


class PublicProductSchema(ProductSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductsList(BaseModel):
    products: list[PublicProductSchema]


class ExtractResultSchema(BaseModel):
    id: int
    extracted: bool
    document_path: HttpUrl
    created_at: datetime
    extract_result: str


class ProductInfoByAIResponse(ProductSchema):
    document_id: int
    individual_quantity: int # TODO: adicionar no produto normal

