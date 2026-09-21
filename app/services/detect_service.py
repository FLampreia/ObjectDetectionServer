import time
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy.orm import Session
from fastapi import UploadFile
import json
from app.core.config import config
from app.db.schema import Detection, DetectedObject, DetectionType
from app.models.detect import FrameProcessingResponse, VideoProcessingResponse
from app.services.user_service import UserService


class DetectService:

    def __init__(
            self,
            session: Session,
    ):
        self._db = session

    def add_detection_to_db(
            self,
            user_id: UUID,
            team_id: UUID,
            model: str,
            conf_threshold: float,
            created_at: datetime,
            result: FrameProcessingResponse,
            detection_type: DetectionType
    ):
        detection = Detection(
            user_id=user_id,
            team_id=team_id,
            model=model,
            conf_threshold=conf_threshold,
            processing_time_ms=result.processing_time_per_frame,
            created_at=created_at,
            type=detection_type
        )

        self._db.add(detection)
        self._db.flush()

        for obj in result.detections_per_frame:
            detected_object = DetectedObject(
                detection_id=detection.id,
                object_name=obj.class_name,
                object_class_id=obj.class_id,
                confidence=obj.confidence,
            )

            self._db.add(detected_object)

        self._db.commit()

    def add_video_detection_to_db(
            self,
            user_id: UUID,
            team_id: UUID,
            model: str,
            conf_threshold: float,
            created_at: datetime,
            detection_type: DetectionType,
            result: VideoProcessingResponse,
    ):

        detection = Detection(
            user_id=user_id,
            team_id=team_id,
            model=model,
            conf_threshold=conf_threshold,
            processing_time_ms=result.processing_time,
            created_at=created_at,
            type=detection_type,
        )

        self._db.add(detection)
        self._db.flush()

        for obj in result.detections_per_frame:
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
                        "image",
                        (
                            image.filename,
                            image.file,
                            image.content_type,
                        )
                    )
                ],
            )

        response.raise_for_status()

        result = FrameProcessingResponse(**response.json())

        self.add_detection_to_db(
            user_id=current_user_id,
            team_id=chosen_team_id,
            model=algorithm,
            conf_threshold=float(conf_threshold),
            created_at=created_at,
            result=result,
            detection_type=DetectionType.Photo,
        )

        return response.json()

    #
    # async def process_video(
    #         self,
    #         video: UploadFile,
    #         current_user_id: UUID,
    #         conf_threshold: str,
    #         algorithm: str,
    #         chosen_team_id: UUID | None = None,
    #         chosen_class_id: list[str] | None = None,
    #         #TODO fazer area
    # ):
    #
    #
    #     async with httpx.AsyncClient() as client:
    #         response = await client.post(
    #             f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/detect/video",
    #             data={
    #                 "algorithm": algorithm,
    #                 "conf_threshold": conf_threshold,
    #                 "chosen_class_id": chosen_class_id,
    #             },
    #             files=[
    #                 (
    #                     "video",
    #                     (
    #                         video.filename,
    #                         video.file,
    #                         video.content_type,
    #                     )
    #                 )
    #             ],
    #         )
    #
    #     response.raise_for_status()

    async def get_models_list(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/models",
            )

        data = response.json()

        return data

    async def download_model(self, model_name: str):
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/models/{model_name}",
            )

            response.raise_for_status()
            return response.json()

    async def ask_to_create_session(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/socket/session/create",
            )

            response.raise_for_status()
            return response.json()
