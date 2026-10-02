import logging

from fastapi import APIRouter, Depends

from app.core.deps import get_detect_service
from app.core.token import get_current_user
from app.services.processor_service import DetectService

socket_router = APIRouter()
logger = logging.getLogger(__name__)


@socket_router.post("/socket/session")
async def get_socket_connection_to_worker(
        service: DetectService = Depends(get_detect_service),
        current_user=Depends(get_current_user)
):
    logging.info("Asking the worker to create a socket session. Waiting for the processing worker to create it...")

    try:
        result = await service.ask_to_create_session()

        logging.info("Session created with success")

        return result

    except Exception as e:
        logging.warning("Something went wrong.")
        raise

