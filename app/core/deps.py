from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.team_service import TeamService
from app.services.user_service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(session=db)

def get_team_service(db: Session = Depends(get_db)) -> TeamService:
    return TeamService(session=db)
