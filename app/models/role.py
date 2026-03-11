from typing import Optional

from pydantic import BaseModel


class RoleModel(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class RoleCreateModel(BaseModel):
    name: str
    description: Optional[str] = None