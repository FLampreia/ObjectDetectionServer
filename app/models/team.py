import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.schema import TeamRole


class TeamRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

class TeamCreateAndUpdate(BaseModel):
    name: str = Field(min_length=1)

class AddTeamMember(BaseModel):
    email: str
    role: TeamRole = TeamRole.Member

class RemoveTeamMember(BaseModel):
    email: str

class TeamMember(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole