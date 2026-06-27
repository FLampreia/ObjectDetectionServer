import logging
from typing import Optional
from uuid import UUID
import httpx
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.params import Query, Form

from app.core.deps import get_detect_service
from app.core.token import get_current_user
from app.models.detect import DownloadModelRequest
from app.services.detect_service import DetectService

detect_router = APIRouter()
logger = logging.getLogger(__name__)

@detect_router.post("/detect/image")
async def detect_image(
        algorithm: str = Form(...),
        conf_threshold: str = Form(...),
        image: UploadFile = File(...),
        chosen_class_id: list[str] | None = Form(None),
        chosen_team_id: UUID | None = Form(None),

        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user),

):
    logging.info("Received image on server. Sending it to detection...")

    chosen_class_id = [
        c for c in (chosen_class_id or [])
        if c and c.strip()
    ]

    return await service.process_image(
        image=image,
        current_user_id=current_user.id,
        conf_threshold=conf_threshold,
        chosen_team_id=chosen_team_id,
        chosen_class_id=chosen_class_id,
        algorithm=algorithm
    )

@detect_router.get("/detect/models")
async def get_models_list(
        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user)
):
    logging.info("Asking for models on server. Waiting for the processing worker to send them...")

    return await service.get_models_list()

@detect_router.post("/detect/models/download")
async def get_models_list(
        payload: DownloadModelRequest,
        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user)
):
    logging.info("Asking to download a model. Waiting for the processing worker to download it...")

    result = await service.download_model(payload.name)

    return {"status": "ok", "result": result}