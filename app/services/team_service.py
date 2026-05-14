from sqlalchemy.orm import Session
from uuid import UUID

from app.db.schema import TeamRole, Team, TeamMember, User
from app.exceptions.custom_exceptions import UserNotFound, UserAlreadyInTeam, NotTeamOwner, NotAllowedToRemoveOwner
from app.services.user_service import UserService


class TeamService:

    def __init__(
        self,
        session: Session,
        user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

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

    def delete_team(self, team_id: UUID, requester_id: UUID) -> bool:

        self._validate_owner(team_id, requester_id)

        team = self.get_team(team_id)
        if not team:
            return False

        self._db.delete(team)
        self._db.commit()

        return True

    def add_member_to_team(
            self,
            team_id: UUID,
            email: str,
            role: TeamRole,
            requester_id: UUID
    ):

        self._validate_owner(team_id, requester_id)

        user = self._user_service.get_user_by_email(email)

        if not user:
            raise UserNotFound()

        existing = self._get_member(team_id, user.id)

        if existing:
            raise UserAlreadyInTeam()

        membership = TeamMember(
            team_id=team_id,
            user_id=user.id,
            role=role
        )

        self._db.add(membership)
        self._db.commit()

        return membership

    def remove_member_from_team(self, team_id: UUID, email: str, requester_id: UUID):

        self._validate_owner(team_id, requester_id)

        user = self._user_service.get_user_by_email(email)

        if not user:
            raise UserNotFound()

        membership = self._get_member(team_id, user.id)

        if not membership:
            raise UserNotFound()

        # If owner, check if it's the last one
        if membership.role == TeamRole.Owner:
            owners_count = (
                self._db.query(TeamMember)
                .filter(
                    TeamMember.team_id == team_id,
                    TeamMember.role == TeamRole.Owner
                )
                .count()
            )

            if owners_count <= 1:
                raise NotAllowedToRemoveOwner()

        self._db.delete(membership)
        self._db.commit()

        return True

    def get_team_members(self, team_id: UUID) -> list[type[TeamMember]]:

        return self._db.query(TeamMember).filter(TeamMember.team_id == team_id).all()


    def _validate_owner(self, team_id:UUID, requester_id:UUID):

        team_member = self._get_member(team_id, requester_id)

        if not team_member or team_member.role != TeamRole.Owner:
            raise NotTeamOwner()

    def _get_member(self, team_id: UUID, user_id: UUID) -> TeamMember | None:

        return (
            self._db.query(TeamMember)
            .filter_by(team_id=team_id, user_id=user_id)
            .first()
        )
