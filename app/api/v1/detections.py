import logging
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from starlette import status

from app.core.deps import get_detections_service, get_report_service
from app.core.token import get_current_user
from app.services.detections_service import DetectionService
from app.services.report_service import ReportService

detections_router = APIRouter()
logger = logging.getLogger(__name__)


@detections_router.get("/detections/all", status_code=status.HTTP_200_OK)
def get_detections_objects(
        service: DetectionService = Depends(get_detections_service),
        current_user=Depends(get_current_user)

):
    logger.info("Getting all detections for logged user %s", current_user.id)

    return service.get_all_detection_from_logged_user(current_user)


@detections_router.get("/detections/{detection_id}/objects", status_code=status.HTTP_200_OK)
def get_detections_objects(
        detection_id: uuid.UUID,
        service: DetectionService = Depends(get_detections_service),
        current_user=Depends(get_current_user)

):
    logger.info("Getting objects for detection %s", detection_id)

    return service.get_objects_from_detection(detection_id)


@detections_router.get("/detections/stats", status_code=status.HTTP_200_OK)
def get_detections_stats(
        service: DetectionService = Depends(get_detections_service),
        current_user=Depends(get_current_user)
):
    logger.info("Getting detections stats for logged user %s", current_user.id)

    return service.get_detections_stats(current_user)


@detections_router.get("/report/detection/interval")
def generate_report_interval(
        start_date: date = Query(...),
        end_date: date = Query(...),
        service: ReportService = Depends(get_report_service),
        current_user=Depends(get_current_user),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date",
        )

    logger.info(
        "Generating detection report for user %s from %s to %s",
        current_user.id,
        start_date,
        end_date,
    )

    return service.generate_report_interval(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@detections_router.get("/report/detection/{detection_id}")
def generate_detection_report(
        detection_id: uuid.UUID,
        service: ReportService = Depends(get_report_service),
        current_user=Depends(get_current_user),
):
    logger.info(
        f"Generating detection report for detection {detection_id} "
    )

    return service.generate_detection_report(
        detection_id=detection_id,
    )
