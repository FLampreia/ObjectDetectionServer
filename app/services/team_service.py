from sqlite3 import IntegrityError

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session, Mapped, joinedload
from uuid import UUID

from app.db.schema import TeamRole, Team, TeamMember, User
from app.exceptions.custom_exceptions import UserNotFound, UserAlreadyInTeam, NotTeamOwner, NotAllowedToRemoveOwner, \
    EmailAlreadyExists, UsernameAlreadyExists, DatabaseIntegrityException, TeamNameAlreadyExists, TeamNotFound
from app.models.team import TeamRead, TeamReadWithRole, TeamMemberRead
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

    def list_user_teams(self, user_id: UUID) -> list[TeamReadWithRole]:
        stmt = (
            select(Team, TeamMember)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id)
        )

        results = self._db.execute(stmt).all()

        return [
            TeamReadWithRole(
                id=team.id,
                name=team.name,
                created_at=team.created_at,
                role=membership.role.value,
                is_favorite=membership.is_favorite,
            )
            for team, membership in results
        ]

    def get_team(self, team_id: UUID) -> Team | None:
        return self._db.query(Team).filter(Team.id == team_id).first()

    def create_team(self, name: str, owner_id: UUID) -> TeamRead:
        team = Team(
            name=name
        )

        self._db.add(team)

        try:
            self._db.flush()

            owner_membership = TeamMember(
                team_id=team.id,
                user_id=owner_id,
                role=TeamRole.Owner
            )
            self._db.add(owner_membership)

            self._db.commit()
            self._db.refresh(team)

            return TeamRead(
                id=team.id,
                name=team.name,
                created_at=team.created_at
            )

        # In case data already exists
        except Exception as e:
            self._db.rollback()
            error_message = str(e)

            if "teams.name" in error_message:
                raise TeamNameAlreadyExists()

            raise DatabaseIntegrityException()

    def delete_team(self, team_id: UUID, requester_id: UUID) -> bool:

        team = self.get_team(team_id)
        if not team:
            raise TeamNotFound()

        self._validate_if_is_member(team_id, requester_id)

        self._db.delete(team)
        self._db.commit()

        return True

    def add_member_to_team(
            self,
            team_id: UUID,
            email: EmailStr,
            requester_id: UUID
    ):

        self._validate_if_is_member(team_id, requester_id)

        user = self._user_service.get_user_by_email(email)

        if not user:
            raise UserNotFound()

        existing = self._get_member(team_id, user.id)

        if existing:
            raise UserAlreadyInTeam()

        membership = TeamMember(
            team_id=team_id,
            user_id=user.id,
            role=TeamRole.Member
        )

        self._db.add(membership)
        self._db.commit()

        return membership

    def remove_member_from_team(self, team_id: UUID, user_id: UUID, requester_id: UUID):

        self._validate_if_is_member(team_id, requester_id)

        user = self._user_service.get_user_by_id(user_id)

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

    def get_team_members(self, team_id: UUID, requester_id: UUID) -> list[TeamMemberRead]:

        self._validate_if_is_member(team_id, requester_id)

        members = (
            self._db.query(TeamMember)
            .options(joinedload(TeamMember.user))
            .filter(TeamMember.team_id == team_id)
            .all()
        )

        return [
            TeamMemberRead(
                user_id=member.user.id,
                username=member.user.username,
                email=member.user.email,
                role=member.role
            )
            for member in members
        ]



    def _validate_if_is_member(self, team_id: UUID, requester_id: UUID):

        return self._get_member(team_id, requester_id)

    # def _validate_owner(self, team_id: UUID, requester_id: UUID):
    #
    #     team_member = self._validate_if_is_member(team_id, requester_id)
    #
    #     if not team_member or team_member.role != TeamRole.Owner:
    #         raise NotTeamOwner()

    def _get_member(self, team_id: UUID, user_id: UUID) -> TeamMember | None:

        return (
            self._db.query(TeamMember)
            .filter_by(team_id=team_id, user_id=user_id)
            .first()
        )

    def toggle_favorite(self, team_id: UUID, requester_id: UUID) -> Mapped[bool]:

        member = (
            self._db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == requester_id,
            )
            .first()
        )
        if not member:
            raise TeamNotFound()

        # toggle
        member.is_favorite = not member.is_favorite

        self._db.commit()
        self._db.refresh(member)

        return member.is_favorite

    def update_name(self, team_id: UUID, name: str, user_id: UUID) -> None:
        # 1. garantir que o utilizador pertence à equipa
        membership = (
            self._db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
            .first()
        )


        if not membership:
            raise ValueError("User is not a member of this team")

        # 2. buscar a equipa
        team = (
            self._db.query(Team)
            .filter(Team.id == team_id)
            .first()
        )

        if not team:
            raise ValueError("Team not found")

        # 3. atualizar nome
        team.name = name

        try:
            self._db.commit()
        except IntegrityError:
            self._db.rollback()
            self.error = ValueError("Team name already exists")
            raise self.error
