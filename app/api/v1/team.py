import logging
import uuid

from fastapi import APIRouter, Depends
from starlette import status

from app.core.deps import get_team_service
from app.core.token import get_current_user
from app.models.team import TeamRead, TeamCreateAndUpdate, AddTeamMember, RemoveTeamMember, TeamMember, TeamReadWithRole
from app.models.user import UserRead
from app.services.team_service import TeamService

team_router = APIRouter()
logger = logging.getLogger(__name__)


@team_router.post("/team", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
        team: TeamCreateAndUpdate,
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Creating team with data: %s", team)

    return service.create_team(
        team.name,
        current_user.id
    )


@team_router.get("/team", response_model=list[TeamRead], status_code=status.HTTP_200_OK)
def get_all_team_list(
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Getting team list")

    return service.list_teams()


@team_router.get("/team/logged", response_model=list[TeamReadWithRole], status_code=status.HTTP_200_OK)
def get_logged_user_team_list(
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Getting logged user team list")
    return service.list_user_teams(current_user.id)


@team_router.post("/team/{team_id}/add", response_model=TeamMember, status_code=status.HTTP_200_OK)
def add_team_member(
        team_id: uuid.UUID,
        data: AddTeamMember,
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Adding team member with data: \n\t%s \n To team: \n\t %s", data, team_id)

    return service.add_member_to_team(
        team_id=team_id,
        email=data.email,
        requester_id=current_user.id,
    )


@team_router.delete("/team/{team_id}/remove", status_code=status.HTTP_200_OK)
def remove_team_member(
        team_id: uuid.UUID,
        data: RemoveTeamMember,
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Removing team member with data: \n\t%s \n From team: \n\t %s", data, team_id)

    return service.remove_member_from_team(
        team_id=team_id,
        email=data.email,
        requester_id=current_user.id,
    )


@team_router.get("/team/{team_id}/members", response_model=list[TeamMember], status_code=status.HTTP_200_OK)
def get_team_members(
        team_id: uuid.UUID,
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Getting members from team %s", team_id)

    return service.get_team_members(team_id, current_user.id)


@team_router.delete("/team/{team_id}", status_code=status.HTTP_200_OK)
def delete_team(
        team_id: uuid.UUID,
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Deleting team %s", team_id)

    return service.delete_team(team_id, current_user.id)

@team_router.patch("/team/{team_id}/fav", status_code=status.HTTP_200_OK)
def toggle_fav(
        team_id: uuid.UUID,
        service: TeamService = Depends(get_team_service),
        current_user=Depends(get_current_user)
):
    logger.info("Toggling favorite for team %s", team_id)

    return service.toggle_favorite(team_id, current_user.id)