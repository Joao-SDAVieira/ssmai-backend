from datetime import datetime

from pydantic import BaseModel

from ssmai_backend.schemas.users_schemas import UserAdminSchema


class EnterpryseSchema(BaseModel):
    nome: str
    ramo: str


class EnterpryseResponseModel(EnterpryseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    user_admin: UserAdminSchema
