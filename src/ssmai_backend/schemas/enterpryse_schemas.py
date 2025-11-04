from datetime import datetime

from pydantic import BaseModel, EmailStr

from ssmai_backend.schemas.users_schemas import UserAdminSchema


class EnterpryseBase(BaseModel):
    nome: str
    ramo: str

class EnterpryseSchema(EnterpryseBase):
    email: EmailStr


class EnterpryseGet(EnterpryseBase):
    id: int
    created_at: datetime
    updated_at: datetime


class EnterpryseResponseModel(EnterpryseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    user_admin: UserAdminSchema
