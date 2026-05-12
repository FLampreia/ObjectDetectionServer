from datetime import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    password: str = Field(exclude=True)
    email: str
    full_name: str
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8)
    email: EmailStr
    full_name: str = Field(min_length=1)


class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None