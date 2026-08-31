import uuid
from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.schema import DetectedObject, User, Detection
from app.models.detect import ListObjects, ListDetections
from app.services.user_service import UserService


class DetectionService:

    def __init__(
            self,
            session: Session,
            user_service: UserService
    ):
        self._db = session
        self._user_service = user_service

    def get_all_detection_from_logged_user(
            self,
            current_user: User
    ) -> list[ListDetections]:
        stmt = (
            select(
                Detection.id,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
                func.count(DetectedObject.id).label("count_objects"),
            )
            .outerjoin(
                DetectedObject,
                DetectedObject.detection_id == Detection.id
            )
            .where(Detection.user_id == current_user.id)
            .group_by(
                Detection.id,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
            )
            .order_by(Detection.created_at.desc())
        )

        result = self._db.execute(stmt).all()

        return [
            ListDetections(
                id=r.id,
                username=current_user.username,
                created_at=r.created_at,
                model=r.model,
                conf_threshold=r.conf_threshold,
                processing_time_ms=r.processing_time_ms,
                count=r.count_objects,
                type=r.type,
            )
            for r in result
        ]

    def get_objects_from_detection(
            self,
            detection_id: uuid.UUID,
    ) -> list[ListObjects]:
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