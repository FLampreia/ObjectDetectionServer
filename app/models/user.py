from datetime import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8)
    email: EmailStr
    full_name: str = Field(min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None