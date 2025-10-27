from fastapi_users import schemas
from pydantic import BaseModel


class UserSchemaBase(BaseModel):
    username: str
    name: str
    last_name: str
    description: str
    profile_image: str


class BaseUserSchema(schemas.BaseUserCreate, UserSchemaBase): ...


class UserSchema(schemas.BaseUserCreate, UserSchemaBase):
    id_empresas: int


class UserPublic(schemas.BaseUser[int], UserSchemaBase): ...


class UserAdminSchema(UserSchema):
    id: int | None = None
    clean_password: str
