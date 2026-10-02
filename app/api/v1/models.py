import logging

from fastapi import APIRouter, Depends

from app.core.deps import get_detect_service
from app.core.token import get_current_user
from app.models.detect import DownloadModelRequest
from app.services.processor_service import DetectService

models_router = APIRouter()
logger = logging.getLogger(__name__)


@models_router.get("/models")
async def get_models_list(
        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user)
):
    logging.info("Asking for models on server. Waiting for the processing worker to send them...")

    return await service.get_models_list()


@models_router.post("/models/download")
async def get_models_list(
        payload: DownloadModelRequest,
        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user)
):
    logging.info("Asking to download a model. Waiting for the processing worker to download it...")

    result = await service.download_model(payload.name)

    return {"status": "ok", "result": result}
