from datetime import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, Field



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


class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None