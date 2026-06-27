import time
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy.orm import Session
from fastapi import UploadFile
import json
from app.core.config import config
from app.db.schema import Detection, DetectedObject
from app.models.detect import DetectionResponse
from app.services.user_service import UserService


class DetectService:

    def __init__(
            self,
            session: Session,
            user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

    def add_detection_to_db(
            self,
            user_id: UUID,
            team_id: UUID,
            model: str,
            conf_threshold: float,
            created_at: datetime,
            result: DetectionResponse,
    ):
        detection = Detection(
            user_id=user_id,
            team_id=team_id,
            model=model,
            conf_threshold=conf_threshold,
            processing_time_ms=result.processing_time_ms,
            created_at=created_at,
        )

        self._db.add(detection)
        self._db.flush()

        for obj in result.detections:
            detected_object = DetectedObject(
                detection_id=detection.id,
                object_name=obj.class_name,
                object_class_id=obj.class_id,
                confidence=obj.confidence,
            )

            self._db.add(detected_object)

        self._db.commit()


    async def process_image(
            self,
            image: UploadFile,
            current_user_id: UUID,
            conf_threshold: str,
            algorithm: str,
            chosen_team_id: UUID | None = None,
            chosen_class_id: list[str] | None = None,
    ):
        created_at = datetime.now()

        content = await image.read()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/detect/image",
                data={
                    "algorithm": algorithm,
                    "conf_threshold": conf_threshold,
                    "chosen_class_id": chosen_class_id,
                },
                files=[
                    (
                        "file",
                        (
                            image.filename,
                            content,
                            image.content_type,
                        )
                    )
                ],
            )

        response.raise_for_status()

        result = DetectionResponse(**response.json())

        self.add_detection_to_db(
            user_id=current_user_id,
            team_id=chosen_team_id,
            model=algorithm,
            conf_threshold=float(conf_threshold),
            created_at=created_at,
            result=result
        )

        return response.json()

    async def get_models_list(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/detect/models",
            )

        data = response.json()

        return data

    async def download_model(self, model_name: str):
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/detect/models/{model_name}",
            )

            response.raise_for_status()
            return response.json()
