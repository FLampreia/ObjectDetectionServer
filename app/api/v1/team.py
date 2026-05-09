import logging

from fastapi import APIRouter, Depends

from app.core.deps import get_team_service
from app.core.token import get_current_user
from app.models.team import TeamRead, TeamCreateAndUpdate
from app.models.user import UserRead
from app.services.team_service import TeamService

team_router = APIRouter()
logger = logging.getLogger(__name__)

@team_router.post("/team", response_model=TeamRead)
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