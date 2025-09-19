from fastapi_users import schemas
from pydantic import BaseModel

# class UserSchema(BaseModel):
#     username: str
#     name: str
#     last_name: str
#     description: str
#     profile_image: str
#     is_verified: bool = False
#     email: EmailStr
#     password: str
#     is_active: bool = True
#     is_superuser: bool = False


class UserSchemaBase(BaseModel):
    username: str
    name: str
    last_name: str
    description: str
    profile_image: str


class UserSchema(schemas.BaseUserCreate, UserSchemaBase): ...


class UserPublic(schemas.BaseUser[int], UserSchemaBase): ...
