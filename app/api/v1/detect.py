import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File
from fastapi.params import Depends, Query, Form

from app.core.deps import get_detect_service
from app.core.token import get_current_user
from app.services.detect_service import DetectService

detect_router = APIRouter()
logger = logging.getLogger(__name__)

@detect_router.post("/detect/image")
async def detect_image(
        image: UploadFile = File(...),
        chosen_class_id: Optional[list[int]] = Form(None),
        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user)
):
    logging.info("Received image on server. Sending it to detection...")

    # parsed_classes = None
    # if chosen_class_id:
    #     parsed_classes = json.loads(chosen_class_id)

    return await service.process_image(image, chosen_class_id)