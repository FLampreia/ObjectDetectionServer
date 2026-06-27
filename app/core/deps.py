from fastapi import Depends, Request
import httpx
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.detect_service import DetectService
from app.services.team_service import TeamService
from app.services.user_service import UserService


def get_user_service(
        db: Session = Depends(get_db)
) -> UserService:
    return UserService(session=db)

def get_team_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
) -> TeamService:
    return TeamService(session=db, user_service=user_service)

def get_detect_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ) -> DetectService:
    return DetectService(session=db, user_service=user_service)
