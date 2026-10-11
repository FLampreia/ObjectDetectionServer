from sqlite3 import IntegrityError

from pydantic import EmailStr
from sqlalchemy import select, func
from sqlalchemy.orm import Session, Mapped, joinedload, selectinload
from uuid import UUID

from app.db.schema import TeamRole, Team, TeamMember, User, Detection, DetectedObject
from app.exceptions.custom_exceptions import UserNotFound, UserAlreadyInTeam, NotTeamOwner, NotAllowedToRemoveOwner, \
    EmailAlreadyExists, UsernameAlreadyExists, DatabaseIntegrityException, TeamNameAlreadyExists, TeamNotFound
from app.models.detect import ListDetections
from app.models.team import TeamRead, TeamReadWithFavorite, TeamMemberRead
from app.services.user_service import UserService


class TeamService:

    def __init__(
            self,
            session: Session,
            user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

    def list_teams(self) -> list[TeamRead]:
        teams = (
            self._db.query(Team)
            .options(selectinload(Team.members).selectinload(TeamMember.user))
            .all()
        )

        result = []

        for team in teams:
            owner_membership = next(
                (m for m in team.members if m.role == TeamRole.Owner),
                None
            )

            if owner_membership is None:
                continue  # todo ou lança erro se owner for obrigatório

            result.append(
                TeamRead(
                    id=team.id,
                    name=team.name,
                    created_at=team.created_at,
                    owner=TeamMemberRead(
                        user_id=owner_membership.user.id,
                        username=owner_membership.user.username,
                        email=owner_membership.user.email,
                        role=owner_membership.role,
                    )
                )
            )

        return result

    def list_user_teams(self, user_id: UUID) -> list[TeamReadWithFavorite]:
        stmt = (
            select(Team, TeamMember, User)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .join(User, User.id == TeamMember.user_id)
            .where(TeamMember.user_id == user_id)
        )

        results = self._db.execute(stmt).all()

        team_ids = [team.id for team, _, _ in results]

        owners_stmt = (
            select(TeamMember, User)
            .join(User, User.id == TeamMember.user_id)
            .where(
                TeamMember.team_id.in_(team_ids),
                TeamMember.role == TeamRole.Owner
            )
        )

        owners = {
            tm.team_id: TeamMemberRead(
                user_id=u.id,
                username=u.username,
                email=u.email,
                role=tm.role
            )
            for tm, u in self._db.execute(owners_stmt).all()
        }

        return [
            TeamReadWithFavorite(
                id=team.id,
                name=team.name,
                created_at=team.created_at,
                is_favorite=membership.is_favorite,
                owner=owners.get(team.id),
                current_user_role=membership.role
            )
            for team, membership, _ in results
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
                created_at=team.created_at,
                owner=TeamMemberRead(
                    user_id=owner_membership.user.id,
                    username=owner_membership.user.username,
                    email=owner_membership.user.email,
                    role=owner_membership.role,
                )
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

        user = self._user_service.get_user(user_id)

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
        # 1. Ensure the user belongs to the team.
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

        # 2. Fetch the team.
        team = (
            self._db.query(Team)
            .filter(Team.id == team_id)
            .first()
        )

        if not team:
            raise ValueError("Team not found")

        # 3. Update the name.
        team.name = name

        try:
            self._db.commit()
        except IntegrityError:
            self._db.rollback()
            self.error = ValueError("Team name already exists")
            raise self.error

    def get_detections_from_team_id(self, team_id: UUID) -> list[ListDetections]:
        stmt = (
            select(
                Detection.id,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
                User.username,
                func.count(DetectedObject.id).label("count_objects")
            )
            .join(User, User.id == Detection.user_id)
            .outerjoin(DetectedObject, DetectedObject.detection_id == Detection.id)
            .where(Detection.team_id == team_id)
            .group_by(
                Detection.id,
                User.username
            )
            .order_by(Detection.created_at.desc())
        )

        result = self._db.execute(stmt).all()

        return [
            ListDetections(
                id=r.id,
                username=r.username,
                created_at=r.created_at,
                model=r.model,
                conf_threshold=r.conf_threshold,
                processing_time_ms=r.processing_time_ms,
                count=r.count_objects,
                type=r.type,
            ) for r in result
        ]
