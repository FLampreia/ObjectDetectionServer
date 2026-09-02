import uuid
from datetime import datetime, time
from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.schema import DetectedObject, User, Detection
from app.models.detect import ListObjects, ListDetections
from app.models.stats import ModelsUsage, DetectionTypeUsage, TopObject, Stats
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

    def get_detections_stats(
            self,
            current_user: User,
    ) -> Stats:
        # Total de deteções
        total_detections = self._db.scalar(
            select(func.count(Detection.id))
            .where(Detection.user_id == current_user.id)
        ) or 0

        # Total de objetos detetados
        total_objects = self._db.scalar(
            select(func.count(DetectedObject.id))
            .join(
                Detection,
                Detection.id == DetectedObject.detection_id,
            )
            .where(Detection.user_id == current_user.id)
        ) or 0

        # Objetos mais detetados
        top_objects_result = self._db.execute(
            select(
                DetectedObject.object_name,
                func.count(DetectedObject.id).label("count"),
            )
            .join(
                Detection,
                Detection.id == DetectedObject.detection_id,
            )
            .where(Detection.user_id == current_user.id)
            .group_by(DetectedObject.object_name)
            .order_by(func.count(DetectedObject.id).desc())
            .limit(5)
        ).all()

        top_objects = [
            TopObject(
                name=row.object_name,
                count=row.count,
            )
            for row in top_objects_result
        ]

        # Modelos mais utilizados
        top_models_result = self._db.execute(
            select(
                Detection.model,
                func.count(Detection.id).label("count"),
            )
            .where(Detection.user_id == current_user.id)
            .group_by(Detection.model)
            .order_by(func.count(Detection.id).desc())
            .limit(5)
        )

        top_models = [
            ModelsUsage(
                name=row.model,
                count=row.count,
            )
            for row in top_models_result
        ]

        # Contagem dos tipos de deteções
        detection_types = self._db.execute(
            select(
                Detection.type,
                func.count(Detection.id).label("count"),
            )
            .where(Detection.user_id == current_user.id)
            .group_by(Detection.type)
            .order_by(func.count(Detection.id).desc())
            .limit(3)
        )

        detection_types = [
            DetectionTypeUsage(
                type=row.type,
                count=row.count,
            )
            for row in detection_types
        ]


        # Últimas deteções
        last_detections_result = self._db.execute(
            select(
                Detection.id,
                User.username,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                func.count(DetectedObject.id).label("count"),
                Detection.type,
            )
            .join(
                User,
                User.id == Detection.user_id,
            )
            .outerjoin(
                DetectedObject,
                DetectedObject.detection_id == Detection.id,
            )
            .where(Detection.user_id == current_user.id)
            .group_by(
                Detection.id,
                User.username,
                Detection.created_at,
                Detection.model,
                Detection.conf_threshold,
                Detection.processing_time_ms,
                Detection.type,
            )
            .order_by(Detection.created_at.desc())
            .limit(5)
        ).all()

        last_detections = [
            ListDetections(
                id=row.id,
                username=row.username,
                created_at=row.created_at,
                model=row.model,
                conf_threshold=row.conf_threshold,
                processing_time_ms=row.processing_time_ms,
                count=row.count,
                type=row.type,
            )
            for row in last_detections_result
        ]

        return Stats(
            total_detections=total_detections,
            total_objects=total_objects,

            top_objects=top_objects,
            top_models=top_models,
            detection_types=detection_types,

            last_detections=last_detections,
        )
