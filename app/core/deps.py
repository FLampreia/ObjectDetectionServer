from fastapi import Depends, Request
import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.detect import Area
from app.services.processor_service import DetectService
from app.services.detections_service import DetectionService
from app.services.report_service import ReportService
from app.services.socket_service import SocketService
from app.services.team_service import TeamService
from app.services.user_service import UserService
from fastapi import Form, HTTPException

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
    ) -> DetectService:
    return DetectService(session=db)

def get_detections_service(
        db: Session = Depends(get_db),
) -> DetectionService:
    return DetectionService(session=db)

def get_report_service(
        db: Session = Depends(get_db),
        detection_service: DetectionService = Depends(get_detections_service),
) -> ReportService:
    return ReportService(session=db, detection_service=detection_service)

def get_socket_service() -> SocketService:
    return SocketService()

# Dependency to parse the area from the request body
def parse_area(area: str | None = Form(None)) -> Area | None:
    if area is None:
        return None

    try:
        return Area.model_validate_json(area)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "area", *error["loc"]],
                    "msg": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ],
        ) from exc
