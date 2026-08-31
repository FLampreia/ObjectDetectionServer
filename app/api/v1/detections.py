import logging
import uuid

from fastapi import APIRouter, Depends
from starlette import status

from app.core.deps import get_detections_service
from app.core.token import get_current_user
from app.services.detections_service import DetectionService

detections_router = APIRouter()
logger = logging.getLogger(__name__)

@detections_router.get("/detections/all", status_code=status.HTTP_200_OK)
def get_detections_objects(
        service: DetectionService = Depends(get_detections_service),
        current_user = Depends(get_current_user)

):

    logger.info("Getting all detections for logged user %s", current_user.id)
    # print(service.get_all_detection_from_logged_user(current_user))
    return service.get_all_detection_from_logged_user(current_user)

@detections_router.get("/detections/{detection_id}/objects", status_code=status.HTTP_200_OK)
def get_detections_objects(
        detection_id: uuid.UUID,
        service: DetectionService = Depends(get_detections_service),
        current_user=Depends(get_current_user)

):

    logger.info("Getting objects for detection %s", detection_id)

    return service.get_objects_from_detection(detection_id)