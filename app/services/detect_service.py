import httpx
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.core.config import config
from app.services.user_service import UserService


class DetectService:

    def __init__(
            self,
            session: Session,
            user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

    async def process_image(
            self,
            image: UploadFile,
            chosen_class_id: list[int] | None = None,
    ):
        content = await image.read()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/detect/image",
                files={
                    "file": (image.filename, content, image.content_type)
                }
            )

            return response.json()
