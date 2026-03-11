from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.models.role import RoleModel


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    password: str = Field(exclude=True)
    email: str
    full_name: str
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str


class UserLoginModel(BaseModel):
    email: str
    password: str


class UserWithRoleModel(BaseModel):
    id: uuid.UUID
    username: str
    password: str = Field(exclude=True)
    email: str
    full_name: str
    created_at: datetime

    role: RoleModel

    class Config:
        from_attributes = True
