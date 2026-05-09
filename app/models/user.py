from datetime import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.db.schema import Role


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    password: str = Field(exclude=True)
    email: str
    full_name: str
    created_at: datetime
    role: Role


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None # todo verificar se vale a pena ter aqui o update email visto que podera ser uma cosia que nao será utilizada
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Role] = None
    current_password: Optional[str] = None