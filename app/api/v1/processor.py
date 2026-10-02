import json
from datetime import datetime
import logging
from http.client import responses
from typing import Optional
from uuid import UUID
import httpx
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.params import Query, Form
from fastapi import status

from app.core.deps import get_detect_service, parse_area
from app.core.token import get_current_user
from app.db.schema import DetectionType
from app.models.detect import DownloadModelRequest, FrameProcessingResponse, VideoProcessingResponse, Area
from app.services.processor_service import DetectService
from fastapi import HTTPException
from pydantic import ValidationError

from app.services.cloudinary_service import upload_image


detect_router = APIRouter()
logger = logging.getLogger(__name__)


@detect_router.post("/detect/image", status_code=status.HTTP_200_OK, response_model=FrameProcessingResponse)
async def detect_image(
        algorithm: str = Form(...),
        conf_threshold: str = Form(...),
        image: UploadFile = File(...),
        chosen_class_id: list[str] | None = Form(None),
        chosen_team_id: UUID | None = Form(None),
        area: Area | None = Depends(parse_area),

        detect_service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user),

):
    logging.info("Received image on server.")

    # Upload image to Cloudinary
    try:
        uploaded = await upload_image(image)
    except Exception:
        logger.error("Failed uploading image to Cloudinary.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="It was not possible to save the image on Cloudinary.",
        )

    logging.info("Sending it to detection...")

    try:
        # Process image
        return await detect_service.process_image(
            image=image,
            current_user_id=current_user.id,
            conf_threshold=conf_threshold,
            chosen_team_id=chosen_team_id,
            chosen_class_id=chosen_class_id,
            algorithm=algorithm,
            area=area,
            image_public_id=uploaded["public_id"],
            image_url=uploaded["secure_url"],
        )
    except Exception:
        logger.exception("Failed processing image.")
        raise HTTPException(
            status_code=500,
            detail="It was not possible to process the image.",
        )


@detect_router.post("/save/detections", status_code=status.HTTP_200_OK)
async def save_detections_to_db(
        result: VideoProcessingResponse,
        algorithm: str,
        conf_threshold: float,
        detection_type: str,
        chosen_team_id: UUID | None = None,

        detect_service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user),
):
    logging.info("Received detection data on server. Storing detections on database...")

    if detection_type == "video":
        choosen_type = DetectionType.Video
    elif detection_type == "stream":
        choosen_type = DetectionType.Stream
    else:
        raise ValueError(f"Invalid detection type: {type}")

    try:
        detect_service.add_video_detection_to_db(
            user_id=current_user.id,
            team_id=chosen_team_id,
            model=algorithm,
            conf_threshold=conf_threshold,
            created_at=datetime.now(),
            result=result,
            detection_type=choosen_type,
        )

    except Exception as e:
        logging.error("Error occurred on storing: %s", e)

#
#
# @detect_router.post("/detect/video")
# async def detect_video(
#         algorithm: str = Form(...),
#         conf_threshold: str = Form(...),
#         video: UploadFile = File(...),
#         chosen_class_id: list[str] | None = Form(None),
#         chosen_team_id: UUID | None = Form(None),
#
#         detect_service: DetectService = Depends(get_detect_service),
#         current_user=Depends(get_current_user),
# ):
#     logging.info("Received video on server. Sending it to detection...")
#     try:
#         return await detect_service.process_video(
#             video=video,
#             current_user_id=current_user.id,
#             conf_threshold=conf_threshold,
#             chosen_team_id=chosen_team_id,
#             chosen_class_id=chosen_class_id,
#             algorithm=algorithm
#         )
#     except Exception as e:
#         logging.error("Error occurred on detection: %s", e)
