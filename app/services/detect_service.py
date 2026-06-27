import time
from uuid import UUID

import httpx
from sqlalchemy.orm import Session
from fastapi import UploadFile
import json
from app.core.config import config
from app.db.schema import Detection
from app.services.user_service import UserService


class DetectService:

    def __init__(
            self,
            session: Session,
            user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

    def add_detection(self, user_id: UUID, team_id: UUID):
        print("A guardar deteção")

        # detection = Detection(
        #     user_id=user_id,
        #     team_id=team_id,
        # )

    async def process_image(
            self,
            image: UploadFile,
            current_user_id: UUID,
            conf_threshold: str,
            algorithm: str,
            chosen_team_id: UUID | None = None,
            chosen_class_id: list[str] | None = None,
    ):
        # created_at = time.time()
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

        return response.json()

        # data = [
        #     ("algorithm", algorithm),
        #     ("conf_threshold", conf_threshold),
        # ]
        #
        # if chosen_team_id:
        #     data.append(("chosen_team_id", str(chosen_team_id)))
        #
        # if chosen_class_id:
        #     for class_id in chosen_class_id:
        #         data.append(("chosen_class_id", str(class_id)))
        # print(data)

        # async with httpx.AsyncClient(timeout=60.0) as client:
        #     response = await client.post(
        #         f"http://{config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}/detect/image",
        #         data=data,
        #         files={"file": (image.filename, content, image.content_type)},
        #     )
        #     response.raise_for_status()
        #
        # response = response.json()
        # print(response)
        # # print(created_at)
        # # self.add_detection(current_user_id, chosen_team_id, agorithm)
        #
        # return response

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
