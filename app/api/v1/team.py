import logging
import uuid

from fastapi import APIRouter, Depends
from starlette import status

from app.core.deps import get_team_service
from app.core.token import get_current_user
from app.models.team import TeamRead, TeamCreateAndUpdate, AddTeamMember
from app.models.user import UserRead
from app.services.team_service import TeamService

team_router = APIRouter()
logger = logging.getLogger(__name__)

@team_router.post("/team", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
        team: TeamCreateAndUpdate,
        service: TeamService = Depends(get_team_service),
        current_user = Depends(get_current_user)
):
    logger.info("Creating team with data: %s", team)

    return service.create_team(
        team.name,
        current_user.id
    )
@team_router.get("/team", response_model=list[TeamRead], status_code=status.HTTP_200_OK)
def get_team_list(
        service: TeamService = Depends(get_team_service),
        current_user = Depends(get_current_user)
):
    logger.info("Getting team list")

    return service.list_teams()
@team_router.post("/team/{team_id}/add", status_code=status.HTTP_200_OK)
def add_team_member(
        team_id: uuid.UUID,
        data: AddTeamMember,
        service: TeamService = Depends(get_team_service),
        current_user = Depends(get_current_user)
):
    logger.info("Adding team member with data: \n\t%s \n To team: \n\t %s", data, team_id)

    return service.add_member_to_team(
        team_id=team_id,
        email=data.email,
        role=data.role,
        requester_id=current_user.id,
    )