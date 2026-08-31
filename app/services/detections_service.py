import uuid
from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.schema import DetectedObject
from app.models.detect import ListObjects
from app.services.user_service import UserService


class DetectionService:

    def __init__(
            self,
            session: Session,
            user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

    def get_objects_from_detection(
            self,
            detection_id: uuid.UUID,
    ) -> List[ListObjects]:
        stmt = (
            select(
                DetectedObject.id,
                DetectedObject.object_name,
                DetectedObject.object_class_id,
                DetectedObject.confidence,
            )
            .where(DetectedObject.detection_id == detection_id)
        )

        result = self._db.execute(stmt).all()

        return [
            ListObjects(
                id=r.id,
                obj_name=r.object_name,
                obj_class_id=r.object_class_id,
                confidence=r.confidence,
            ) for r in result
        ]