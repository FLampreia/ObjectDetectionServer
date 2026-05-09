from sqlalchemy.orm import Session
from uuid import UUID

from app.db.schema import TeamRole, Team, TeamMember
from app.exceptions.custom_exceptions import DatabaseIntegrityException


class TeamService:

    def __init__(self, session:Session):
        self._db = session

    def list_teams(self) -> list[type[Team]]:
        return self._db.query(Team).all()

    def get_team(self, team_id: UUID) -> Team | None:
        return self._db.query(Team).filter(Team.id == team_id).first()

    def create_team(self, name: str, owner_id: UUID) -> Team:
        team = Team(
            name=name
        )

        self._db.add(team)
        self._db.flush()

        owner_membership = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role=TeamRole.Owner
        )

        self._db.add(owner_membership)

        self._db.commit()
        self._db.refresh(team)

        return team

    def delete_team(self, team_id: UUID) -> bool:
        team = self.get_team(team_id)
        if not team:
            return False
        self._db.delete(team)
        self._db.commit()
        return True
