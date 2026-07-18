import uuid
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.db.schema import TeamRole

class TeamMemberRead(BaseModel):
    user_id: uuid.UUID
    username: str
    email: EmailStr
    role: TeamRole

    class Config:
        from_attributes = True

class TeamRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    owner: TeamMemberRead

class TeamCreateAndUpdate(BaseModel):
    name: str = Field(min_length=1)

class AddTeamMember(BaseModel):
    email: EmailStr

class RemoveTeamMember(BaseModel):
    user_id: uuid.UUID

class TeamMember(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole


class TeamReadWithFavorite(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    is_favorite: bool
    owner: TeamMemberRead
    current_user_role: TeamRole
