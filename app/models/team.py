import uuid
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.db.schema import TeamRole


class TeamRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

class TeamCreateAndUpdate(BaseModel):
    name: str = Field(min_length=1)

class AddTeamMember(BaseModel):
    email: EmailStr

class RemoveTeamMember(BaseModel):
    email: EmailStr

class TeamMember(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole